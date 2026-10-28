#pragma once
#include "Pattern.h"
#include <vector>

namespace meetstep {
using LedColour = std::array<unsigned char, 4>;
using LedFrame = std::array<LedColour, 32>;
inline constexpr LedColour stepColour {71, 215, 176, 255}; // Same green as the editor.

inline LedFrame ledFrame(const Pattern& model) {
    LedFrame frame {};
    const int note = model.selectedNote(), pattern = model.currentPattern();
    for (int step = 0; step < 16; ++step)
        if (model.enabled(pattern, note, step)) frame[step] = stepColour;
    // Fixed varied colours: no continuous random writes to device configuration.
    constexpr std::array<LedColour, 16> palette {{
        {255, 40, 40, 255}, {255, 128, 0, 255}, {255, 220, 0, 255}, {100, 255, 0, 255},
        {0, 220, 100, 255}, {0, 200, 255, 255}, {40, 80, 255, 255}, {150, 40, 255, 255},
        {255, 0, 160, 255}, {255, 100, 180, 255}, {120, 255, 220, 255}, {160, 180, 255, 255},
        {255, 180, 100, 255}, {190, 255, 80, 255}, {180, 80, 220, 255}, {255, 255, 255, 255}
    }};
    for (int i = 0; i < 16; ++i) frame[i + 16] = palette[i];
    return frame;
}

// Frozen Python tester's "maximum" format: region 5, one RGB+enable block.
// pad is zero-based here, unlike the Python UI's 1..32 labels.
inline std::vector<unsigned char> ledPacketBytes(int pad, LedColour colour) {
    if (pad < 0 || pad >= 32) return {};
    const unsigned address = 0x11b + unsigned(pad) * 0x4a;
    std::vector<unsigned char> data {5};
    for (int i = 0; i < 4; ++i) data.push_back((address >> (8*i)) & 255);
    data.insert(data.end(), {4, 0, 0});
    data.insert(data.end(), colour.begin(), colour.end());
    std::vector<unsigned char> logical {0, 0x59, 0x22, 12, 0, 0};
    unsigned sum = 0;
    for (auto value : data) { logical.push_back(value); sum += value; }
    logical.push_back((~sum) & 255);
    std::vector<unsigned char> wire {0xf0};
    unsigned acc = 0;
    int bits = 0;
    for (auto value : logical) {
        acc |= unsigned(value) << bits; bits += 8;
        while (bits >= 7) { wire.push_back(acc & 127); acc >>= 7; bits -= 7; }
    }
    if (bits) wire.push_back(acc & 127);
    wire.push_back(0xf7);
    return wire;
}

inline bool isPlayStopPad(int channel, int note, int velocity) {
    return channel == 10 && note == Pattern::bank2[8] && velocity > 0 && velocity <= 127;
}
}
