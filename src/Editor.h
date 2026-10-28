#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "Pattern.h"

namespace meetstep {
class Grid : public juce::Component {
public:
    explicit Grid(Pattern& p) : model(p), stroke(p) {}
    int baseNote=36;
    std::atomic<int> playingStep {-1};
    juce::Rectangle<int> cells() const { return getLocalBounds().withTrimmedLeft(92).withTrimmedTop(26); }
    void paint(juce::Graphics& g) override {
        const auto area=cells();
        const float w=area.getWidth()/16.0f, h=area.getHeight()/16.0f;
        g.fillAll(juce::Colour(0xff171b24));
        const char* names[]={"C","C#","D","D#","E","F","F#","G","G#","A","A#","B"};
        for(int s=0;s<16;++s) {
            g.setColour(juce::Colours::lightgrey);
            g.drawText(juce::String(s+1), int(area.getX()+s*w),0,int(w),24,juce::Justification::centred);
        }
        for(int row=0;row<16;++row) {
            const int note=baseNote+15-row;
            g.setColour(note==model.selectedNote()?juce::Colour(0xffffc66d):juce::Colours::lightgrey);
            const auto label=juce::String(names[note%12])+juce::String(note/12-2)+"  ("+juce::String(note)+")";
            g.drawText(label,4,int(area.getY()+row*h),84,int(h),juce::Justification::centredLeft);
            for(int s=0;s<16;++s) {
                g.setColour(model.enabled(note,s)?juce::Colour(0xff47d7b0):
                    (s%4==0?juce::Colour(0xff354152):juce::Colour(0xff272f3d)));
                auto cell=juce::Rectangle<float>(area.getX()+s*w+2,area.getY()+row*h+2,w-4,h-4);
                g.fillRoundedRectangle(cell,3);
                if(s==playingStep.load()) {g.setColour(juce::Colour(0xffffc66d));g.drawRoundedRectangle(cell,3,1.5f);}
            }
        }
    }
    void mouseDown(const juce::MouseEvent& e) override {
        if(!cells().contains(e.getPosition())) return;
        if(!e.mods.isLeftButtonDown() && !e.mods.isRightButtonDown()) return;
        const int row=(e.y-cells().getY())*16/cells().getHeight();
        model.selectNote(baseNote+15-row);
        stroke.begin(baseNote+15-row,stepAt(e.x),!e.mods.isRightButtonDown());
        repaint();
    }
    void mouseDrag(const juce::MouseEvent& e) override {
        stroke.drag(juce::jlimit(0,15,stepAt(e.x))); repaint();
    }
    void mouseUp(const juce::MouseEvent&) override { stroke.end(); }
    void cancelStroke() { stroke.end(); }
private:
    int stepAt(int x) const { return int(std::floor((x-cells().getX())*16.0/cells().getWidth())); }
    Pattern& model;
    GridStroke stroke;
};

class Panel : public juce::Component, private juce::Timer {
public:
    explicit Panel(Pattern& p) : model(p),grid(p) {
        addAndMakeVisible(grid);
        for(int i=0;i<Pattern::count;++i) {
            auto& button=buttons[i];
            button.setButtonText(juce::String(i+1));
            button.setColour(juce::TextButton::buttonOnColourId,juce::Colour(0xff278b78));
            button.onClick=[this,i] { grid.cancelStroke(); model.selectPattern(i); refresh(); };
            addAndMakeVisible(button);
        }
        setup(clearCurrent,"Clear pattern",[this] { grid.cancelStroke(); model.clearCurrent(); refresh(); });
        setup(clearAll,"Clear all",[this] { grid.cancelStroke(); model.clearAll(); refresh(); });
        setup(lower,"-16 notes",[this] { changeRange(-16); });
        setup(higher,"+16 notes",[this] { changeRange(16); });
        refresh(); startTimerHz(30);
    }
    void paint(juce::Graphics& g) override {
        g.fillAll(juce::Colour(0xff171b24));
        g.setColour(juce::Colours::white);
        g.setFont(22.0f); g.drawText("MeetStep",16,8,180,30,juce::Justification::centredLeft);
        g.setFont(13.0f); g.setColour(juce::Colours::lightgrey);
        g.drawText("Left: draw  |  Right: erase  |  Drag: edit one row",16,getHeight()-28,getWidth()-32,24,juce::Justification::centredLeft);
    }
    void resized() override {
        for(int i=0;i<6;++i) buttons[i].setBounds(16+i*46,48,38,38);
        clearCurrent.setBounds(306,48,120,38); clearAll.setBounds(436,48,100,38);
        lower.setBounds(getWidth()-220,48,96,38); higher.setBounds(getWidth()-116,48,100,38);
        grid.setBounds(16,102,getWidth()-32,getHeight()-138);
    }
    Grid& getGrid() { return grid; }
private:
    void setup(juce::TextButton& b,const juce::String& text,std::function<void()> action) {
        b.setButtonText(text); b.onClick=std::move(action); addAndMakeVisible(b);
    }
    void changeRange(int delta) {
        grid.cancelStroke(); grid.baseNote=juce::jlimit(0,112,grid.baseNote+delta); refresh();
    }
    void refresh() {
        for(int i=0;i<6;++i) buttons[i].setToggleState(i==model.currentPattern(),juce::dontSendNotification);
        lower.setEnabled(grid.baseNote>0); higher.setEnabled(grid.baseNote<112); grid.repaint();
    }
    void timerCallback() override { refresh(); }
    Pattern& model;
    Grid grid;
    std::array<juce::TextButton,6> buttons;
    juce::TextButton clearCurrent,clearAll,lower,higher;
};
}
