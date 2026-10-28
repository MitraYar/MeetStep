#pragma once
#include <iostream>

inline bool Main::selfTest() {
    using namespace std::chrono_literals;
    int checks = 0, failures = 0;
    auto check = [&](bool ok, const char* name) {
        ++checks;
        std::cout << (ok ? "PASS " : "FAIL ") << name << '\n';
        if (!ok) ++failures;
    };
    auto until = [](auto condition) {
        const auto deadline = std::chrono::steady_clock::now() + 2s;
        while (!condition()) {
            if (std::chrono::steady_clock::now() >= deadline) return false;
            std::this_thread::sleep_for(1ms);
        }
        return true;
    };
    std::vector<juce::MidiMessage> musical;
    Main app(true); // Does not restore, save, or open any MIDI devices.
    app.observeMidi = [&](const juce::MidiMessage& m) { musical.push_back(m); };
    app.handleIncomingMidiMessage(nullptr, juce::MidiMessage::noteOn(10, 52, (juce::uint8)100));
    check(app.running && musical.back().isMidiStart() && app.model.selectedNote() == -1,
          "pad 25 starts before any drum is selected");
    app.handleIncomingMidiMessage(nullptr, juce::MidiMessage::noteOff(10, 52));
    app.handleIncomingMidiMessage(nullptr, juce::MidiMessage::noteOn(10, 52, (juce::uint8)0));
    check(app.running, "pad release and zero velocity do not toggle");
    app.handleIncomingMidiMessage(nullptr, juce::MidiMessage::noteOn(1, 52, (juce::uint8)100));
    check(app.running && app.model.selectedNote() == 52, "keyboard note 52 selects a drum");
    app.handleIncomingMidiMessage(nullptr, juce::MidiMessage::noteOn(10, 52, (juce::uint8)100));
    check(!app.running && musical.back().isMidiStop(), "pad 25 stops");
    const juce::KeyPress space(juce::KeyPress::spaceKey);
    app.keyPressed(space, &app.start);
    app.keyPressed(space, &app.start);
    check(app.running, "space starts and autorepeat does not toggle again");
    app.keyStateChanged(false, &app.start);
    app.keyPressed(space, &app.stop);
    check(!app.running, "next space press stops even with a button focused");
    app.keyStateChanged(false, &app.stop);
    app.model.setStep(0, 36, 0, true);
    app.start.onClick();
    app.next = 0;
    app.hiResTimerCallback();
    bool clock = false, note = false;
    for (const auto& m : musical) { clock |= m.isMidiClock(); note |= m.isNoteOn() && m.getNoteNumber() == 36; }
    check(clock && note && app.sounding[36], "baseline clock and sequence note are emitted");
    const auto beforeStop = musical.size();
    app.handleIncomingMidiMessage(nullptr, juce::MidiMessage::noteOn(10, 52, (juce::uint8)100));
    bool noteOff = false;
    for (auto i = beforeStop; i < musical.size(); ++i)
        noteOff |= musical[i].isNoteOff() && musical[i].getNoteNumber() == 36;
    check(!app.running && noteOff && app.sounding.none(), "pad stop sends Note Off, then stops transport");
    app.tick = 7; app.resume.onClick();
    check(app.tick == 7 && musical.back().isMidiContinue(), "baseline Continue preserves position");
    app.stop.onClick();

    meetstep::LedFeedback led;
    const auto frame = meetstep::ledFrame(app.model);
    const unsigned char ackBytes[] {0xf0, 0, 0x32, 1, 8, 0, 0, 0, 0, 0x7f, 1, 0xf7};
    const juce::MidiMessage ack(ackBytes, sizeof(ackBytes));
    std::atomic<int> tx {0};
    std::atomic<bool> correct {true};
    led.start([&](const juce::MidiMessage& m) {
        const int index = tx.load();
        const auto expected = meetstep::ledPacketBytes(index, frame[index]);
        if (m.getRawDataSize() != int(expected.size()) || std::memcmp(m.getRawData(), expected.data(), expected.size()) != 0)
            correct = false;
        led.receive(ack); ++tx;
    }, frame, 100ms);
    check(until([&] { return tx == 32; }) && correct, "32 initial Maximum packets in pad order with ACK");
    for (int i = 0; i < 20; ++i) led.update(frame);
    std::this_thread::sleep_for(30ms);
    check(tx == 32 && !led.hasFailed(), "unchanged colours are not resent");
    led.close();

    tx = 0;
    led.start([&](const juce::MidiMessage& m) { ++tx; led.receive(m); }, frame, 30ms);
    check(until([&] { return led.hasFailed(); }) && tx == 1, "echo is not ACK; timeout stops after one packet");
    led.update(frame); std::this_thread::sleep_for(30ms);
    check(tx == 1, "timeout has no automatic retry");
    led.close();

    tx = 0;
    led.start([&](const juce::MidiMessage&) { ++tx; }, frame, 2s);
    check(until([&] { return tx == 1; }), "worker waits for first ACK");
    const auto started = std::chrono::steady_clock::now();
    led.close();
    check(std::chrono::steady_clock::now() - started < 500ms, "close cancels ACK wait promptly");

    tx = 0; correct = true;
    auto changed = frame; changed[3] = meetstep::stepColour;
    led.start([&](const juce::MidiMessage& m) {
        if (tx.load() == 32) {
            const auto expected = meetstep::ledPacketBytes(3, changed[3]);
            if (m.getRawDataSize() != int(expected.size()) || std::memcmp(m.getRawData(), expected.data(), expected.size()) != 0)
                correct = false;
        }
        led.receive(ack); ++tx;
    }, frame, 100ms);
    check(until([&] { return tx == 32; }), "reconnect sends a complete frame");
    led.update(changed);
    check(until([&] { return tx == 33; }) && correct, "editing sends only changed pad with correct bytes");
    led.close();
    std::cout << checks << " checks, " << failures << " failures\n";
    return failures == 0;
}
