#pragma once
#include "LedProtocol.h"
#include <juce_audio_devices/juce_audio_devices.h>
#include <condition_variable>
#include <cstring>
#include <functional>
#include <mutex>
#include <thread>

namespace meetstep {
// One in-flight packet, exact ACK, no retries, no added pause: "maximum".
// The musical clock never waits for this worker.
class LedFeedback : private juce::MidiInputCallback {
public:
    ~LedFeedback() { close(); }
    juce::String open(const juce::String& out, const juce::String& in,
                      bool sharedInput, const LedFrame& initial) {
        close();
        if (out.isEmpty()) return {};
        output = juce::MidiOutput::openDevice(out);
        if (!sharedInput) input = juce::MidiInput::openDevice(in, this);
        if (!output || (!sharedInput && !input)) {
            close(); return "Cannot open LED output / ACK input";
        }
        if (input) input->start();
        start([this](const juce::MidiMessage& message) { output->sendMessageNow(message); }, initial);
        return {};
    }
    void start(std::function<void(const juce::MidiMessage&)> sink, const LedFrame& initial,
               std::chrono::milliseconds timeout = std::chrono::seconds(2)) {
        stopWorker();
        {
            std::lock_guard<std::mutex> guard(mutex);
            quit = false; failed = false; waiting = false; ack = false;
            desired = initial; valid.fill(false); send = std::move(sink); ackTimeout = timeout;
        }
        worker = std::thread([this] { run(); });
    }
    void close() {
        stopWorker();
        if (input) input->stop();
        input.reset(); output.reset();
    }
    void update(const LedFrame& frame) {
        std::lock_guard<std::mutex> guard(mutex); desired = frame; wake.notify_all();
    }
    bool hasFailed() { std::lock_guard<std::mutex> guard(mutex); return failed; }
    void receive(const juce::MidiMessage& message) {
        static const unsigned char expected[] {0xf0, 0, 0x32, 1, 8, 0, 0, 0, 0, 0x7f, 1, 0xf7};
        if (message.getRawDataSize() != sizeof(expected)
            || std::memcmp(message.getRawData(), expected, sizeof(expected)) != 0) return;
        std::lock_guard<std::mutex> guard(mutex);
        if (waiting) { ack = true; wake.notify_all(); }
    }
private:
    void handleIncomingMidiMessage(juce::MidiInput*, const juce::MidiMessage& message) override { receive(message); }
    void stopWorker() {
        { std::lock_guard<std::mutex> guard(mutex); quit = true; }
        wake.notify_all();
        if (worker.joinable()) worker.join();
        std::lock_guard<std::mutex> guard(mutex); waiting = false; failed = false;
    }
    void run() {
        std::unique_lock<std::mutex> guard(mutex);
        while (!quit) {
            int pad = -1;
            for (int i = 0; i < 32; ++i)
                if (!valid[i] || sent[i] != desired[i]) { pad = i; break; }
            if (pad < 0) { wake.wait(guard); continue; }
            const auto colour = desired[pad];
            const auto bytes = ledPacketBytes(pad, colour);
            const juce::MidiMessage message(bytes.data(), int(bytes.size()));
            ack = false; waiting = true;
            guard.unlock(); send(message); guard.lock();
            if (!wake.wait_for(guard, ackTimeout, [this] { return ack || quit; })) {
                waiting = false; failed = true; return;
            }
            waiting = false;
            if (quit) return;
            sent[pad] = colour; valid[pad] = true;
        }
    }
    std::unique_ptr<juce::MidiInput> input;
    std::unique_ptr<juce::MidiOutput> output;
    std::mutex mutex;
    std::condition_variable wake;
    std::thread worker;
    LedFrame desired {}, sent {};
    std::array<bool, 32> valid {};
    bool quit = true, failed = false, waiting = false, ack = false;
    std::function<void(const juce::MidiMessage&)> send;
    std::chrono::milliseconds ackTimeout {2000};
};
}
