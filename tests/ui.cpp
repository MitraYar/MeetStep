#include <juce_audio_processors/juce_audio_processors.h>
#include "Editor.h"
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter();
#include <iostream>
#include <stdexcept>
void check(bool b) { if(!b) throw std::runtime_error("UI assertion failed"); }
int main() {
    juce::ScopedJuceInitialiser_GUI init;
    meetstep::Pattern model;
    meetstep::Panel panel(model); panel.setSize(940,670);
    auto& grid=panel.getGrid();
    auto event=[&](int step,int row,bool right) {
        auto area=grid.cells();
        juce::Point<float> pos(area.getX()+(step+0.5f)*area.getWidth()/16,
                               area.getY()+(row+0.5f)*area.getHeight()/16);
        return juce::MouseEvent(juce::Desktop::getInstance().getMainMouseSource(),pos,
            juce::ModifierKeys(right?juce::ModifierKeys::rightButtonModifier:juce::ModifierKeys::leftButtonModifier),
            1,0,0,0,0,&grid,&grid,juce::Time::getCurrentTime(),pos,juce::Time::getCurrentTime(),1,false);
    };
    auto click=[&](const juce::String& text) {
        for(auto* child:panel.getChildren()) if(auto* b=dynamic_cast<juce::TextButton*>(child))
            if(b->getButtonText()==text) { b->onClick(); return; }
        throw std::runtime_error("Button missing");
    };
    grid.mouseDown(event(0,15,false)); grid.mouseDrag(event(15,0,false)); grid.mouseUp(event(15,0,false));
    for(int s=0;s<16;++s) check(model.enabled(36,s));
    check(!model.enabled(51,15));
    grid.mouseDown(event(0,15,false)); grid.mouseUp(event(0,15,false)); check(model.enabled(36,0));
    grid.mouseDown(event(15,15,true)); grid.mouseDrag(event(0,0,true)); grid.mouseUp(event(0,0,true));
    for(int s=0;s<16;++s) check(!model.enabled(36,s));
    for(int p=0;p<6;++p) { click(juce::String(p+1)); check(model.currentPattern()==p); grid.mouseDown(event(p,0,false)); grid.mouseUp(event(p,0,false)); }
    click("Clear pattern"); check(!model.enabled(5,51,5)); check(model.enabled(4,51,4));
    click("+16 notes"); check(grid.baseNote==52); click("-16 notes"); check(grid.baseNote==36);
    click("Clear all"); for(int p=0;p<6;++p) check(!model.enabled(p,51,p));
    click("1"); model.noteOn(1,36,100);
    for(int s: {0,4,8,12}) model.setStep(0,36,s,true);
    for(int s: {4,12}) model.setStep(0,38,s,true);
    for(int s=0;s<16;s+=2) model.setStep(0,42,s,true);
    auto image=panel.createComponentSnapshot(panel.getLocalBounds());
    juce::File out=juce::File::getCurrentWorkingDirectory().getChildFile("meetstep-editor.png");
    if(auto stream=out.createOutputStream()) { juce::PNGImageFormat png; check(png.writeImageToStream(image,*stream)); }
    else check(false);
    std::unique_ptr<juce::AudioProcessor> processor(createPluginFilter());
    juce::AudioBuffer<float> audio(2,64);
    juce::MidiBuffer midi;
    midi.addEvent(juce::MidiMessage::noteOn(1,36,(juce::uint8)100),0);
    midi.addEvent(juce::MidiMessage::noteOn(10,40,(juce::uint8)100),1);
    processor->processBlock(audio,midi);
    juce::MemoryBlock saved,restored;
    processor->getStateInformation(saved);
    auto xml=juce::AudioProcessor::getXmlFromBinary(saved.getData(),int(saved.getSize()));
    check(xml && xml->getNumChildElements()==1);
    check(xml->getChildElement(0)->getIntAttribute("n")==36);
    check(xml->getChildElement(0)->getIntAttribute("bits")==1);
    std::unique_ptr<juce::AudioProcessor> second(createPluginFilter());
    second->setStateInformation(saved.getData(),int(saved.getSize()));
    second->getStateInformation(restored); check(saved==restored);
    second->setStateInformation("invalid",7);
    second->getStateInformation(restored); check(saved==restored);
    std::cout << "UI clicks, row-locked dragging, six patterns, clear and note paging passed\n";
}
