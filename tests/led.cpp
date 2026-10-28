#include "LedProtocol.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <set>
#include <cstdlib>
void check(bool ok, const char* description) {
    if (!ok) { std::cerr << "FAIL: " << description << '\n'; std::exit(1); }
}
int main(int argc, char** argv) {
    check(argc == 2, "golden fixture path required");
    std::ifstream fixture(argv[1]);
    check(bool(fixture), "golden fixture readable");
    int pad, r, g, b, enable, count = 0;
    std::string hex;
    while (fixture >> pad >> r >> g >> b >> enable >> hex) {
        const auto bytes = meetstep::ledPacketBytes(pad, {static_cast<unsigned char>(r),
            static_cast<unsigned char>(g), static_cast<unsigned char>(b), static_cast<unsigned char>(enable)});
        std::ostringstream actual;
        for (auto value : bytes) actual << std::hex << std::setfill('0') << std::setw(2) << int(value);
        check(actual.str() == hex, "maximum-mode bytes match frozen Python oracle");
        ++count;
    }
    check(fixture.eof() && count == 128, "all 128 golden cases executed");
    check(meetstep::ledPacketBytes(-1, {}).empty() && meetstep::ledPacketBytes(32, {}).empty(), "invalid addresses rejected");
    meetstep::Pattern model;
    auto frame = meetstep::ledFrame(model);
    for (int i = 0; i < 16; ++i) check(frame[i] == meetstep::LedColour{}, "unselected note is black");
    std::set<meetstep::LedColour> colours(frame.begin()+16, frame.end());
    check(colours.size() == 16, "bank two has sixteen distinct colours");
    const auto bankTwo = frame;
    model.noteOn(1, 36, 100); model.setStep(0, 36, 0, true); model.setStep(0, 38, 5, true);
    frame = meetstep::ledFrame(model);
    check(frame[0] == meetstep::stepColour && frame[5] == meetstep::LedColour{}, "selected drum only");
    model.noteOn(1, 38, 100); frame = meetstep::ledFrame(model);
    check(frame[0] == meetstep::LedColour{} && frame[5] == meetstep::stepColour, "keyboard note change refreshes frame");
    model.setStep(0, 36, 2, true);
    check(model.selectedNote() == 38, "mouse-style editing does not select a different drum");
    model.selectPattern(1); frame = meetstep::ledFrame(model);
    for (int i = 0; i < 16; ++i) check(frame[i] == meetstep::LedColour{}, "pattern switch clears old LEDs");
    model.selectPattern(0); model.clearCurrent(); frame = meetstep::ledFrame(model);
    for (int i = 0; i < 16; ++i) check(frame[i] == meetstep::LedColour{}, "clear refreshes LEDs");
    for (int i = 16; i < 32; ++i) check(frame[i] == bankTwo[i], "bank two stays fixed during editing");
    check(meetstep::isPlayStopPad(10, 52, 100), "physical pad 25 is channel 10 note 52");
    check(!meetstep::isPlayStopPad(10, 52, 0) && !meetstep::isPlayStopPad(1, 52, 100)
        && !meetstep::isPlayStopPad(10, 63, 100), "release, keyboard pitch, and pad 32 do not toggle transport");
    std::cout << "128 golden packets; selected-note, pattern, clear, palette and pad-25 checks passed\n";
}
