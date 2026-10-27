#pragma once
#include <array>
#include <atomic>
#include <cstdint>

namespace meetstep {
class Pattern {
public:
    static constexpr int count = 6, steps = 16;
    static constexpr std::array<int, 16> bank1 {
        40,41,42,43,48,49,50,51,36,37,38,39,44,45,46,47
    };
    static constexpr std::array<int, 16> bank2 {
        56,57,58,59,64,65,66,67,52,53,54,55,60,61,62,63
    };
    Pattern() noexcept { clearAll(); }
    void noteOn(int channel, int note, int velocity) noexcept {
        if (channel < 1 || channel > 16 || note < 0 || note > 127
            || velocity <= 0 || velocity > 127) return;
        if (channel != 10) { selected.store(note); return; }
        const auto n = selected.load();
        if (n < 0) return;
        for (int i = 0; i < steps; ++i)
            if (bank1[i] == note) {
                patterns[current.load()][n].fetch_xor(1u << i); return;
            }
    }
    int selectedNote() const noexcept { return selected.load(); }
    int currentPattern() const noexcept { return current.load(); }
    void selectPattern(int index) noexcept {
        if (index >= 0 && index < count) current.store(index);
    }
    bool enabled(int note, int step) const noexcept {
        return enabled(current.load(), note, step);
    }
    bool enabled(int pattern, int note, int step) const noexcept {
        return valid(pattern, note, step)
            && (patterns[pattern][note].load() & (1u << step)) != 0;
    }
    void setStep(int pattern, int note, int step, bool on) noexcept {
        if (!valid(pattern, note, step)) return;
        if (on) patterns[pattern][note].fetch_or(1u << step);
        else patterns[pattern][note].fetch_and(~(1u << step));
    }
    void clearCurrent() noexcept { clear(current.load()); }
    void clearAll() noexcept { for (int p=0; p<count; ++p) clear(p); }
private:
    static bool valid(int p, int n, int s) noexcept {
        return p>=0 && p<count && n>=0 && n<128 && s>=0 && s<steps;
    }
    void clear(int p) noexcept { for (auto& row : patterns[p]) row.store(0); }
    std::atomic<int> selected {-1}, current {0};
    std::array<std::array<std::atomic<std::uint32_t>, 128>, count> patterns;
};

// A drag edits one row and one pattern, including cells skipped by mouse events.
class GridStroke {
public:
    explicit GridStroke(Pattern& p) : pattern(p) {}
    void begin(int note, int step, bool on) {
        active = note>=0 && note<128 && step>=0 && step<16;
        if (!active) return;
        row=note; last=step; value=on; bank=pattern.currentPattern();
        pattern.setStep(bank,row,step,value);
    }
    void drag(int step) {
        if (!active || step<0 || step>=16) return;
        const int direction = step>=last ? 1 : -1;
        for (int s=last;;s+=direction) {
            pattern.setStep(bank,row,s,value);
            if (s==step) break;
        }
        last=step;
    }
    void end() { active=false; }
private:
    Pattern& pattern;
    int row=0,last=0,bank=0;
    bool active=false,value=false;
};
}
