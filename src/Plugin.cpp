#include <juce_audio_processors/juce_audio_processors.h>
#include "Editor.h"

class MeetStepProcessor : public juce::AudioProcessor {
public:
    MeetStepProcessor() : AudioProcessor(BusesProperties().withOutput("Output",juce::AudioChannelSet::stereo(),true)) {}
    const juce::String getName() const override { return "MeetStep"; }
    void prepareToPlay(double,int) override {}
    void releaseResources() override {}
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return true; }
    double getTailLengthSeconds() const override { return 0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int,const juce::String&) override {}
    void processBlock(juce::AudioBuffer<float>& audio,juce::MidiBuffer& midi) override {
        audio.clear();
        for(const auto event:midi) {
            const auto message=event.getMessage();
            if(message.isNoteOn()) model.noteOn(message.getChannel(),message.getNoteNumber(),message.getVelocity());
        }
        // Editing milestone: sequencer scheduling and outgoing MIDI are not implemented yet.
        midi.clear();
    }
    bool hasEditor() const override { return true; }
    class Editor : public juce::AudioProcessorEditor {
    public:
        explicit Editor(MeetStepProcessor& p) : AudioProcessorEditor(p),panel(p.model) {
            addAndMakeVisible(panel); setSize(940,670);
        }
        void resized() override { panel.setBounds(getLocalBounds()); }
    private:
        meetstep::Panel panel;
    };
    juce::AudioProcessorEditor* createEditor() override { return new Editor(*this); }
    void getStateInformation(juce::MemoryBlock& dest) override {
        juce::XmlElement xml("MeetStep"); xml.setAttribute("version",1);
        xml.setAttribute("current",model.currentPattern());
        for(int p=0;p<6;++p) for(int n=0;n<128;++n) {
            int bits=0; for(int s=0;s<16;++s) if(model.enabled(p,n,s)) bits|=1<<s;
            if(bits) { auto* row=xml.createNewChildElement("row"); row->setAttribute("p",p); row->setAttribute("n",n); row->setAttribute("bits",bits); }
        }
        copyXmlToBinary(xml,dest);
    }
    void setStateInformation(const void* data,int size) override {
        auto xml=getXmlFromBinary(data,size);
        if(!xml || !xml->hasTagName("MeetStep") || xml->getIntAttribute("version")!=1) return;
        model.clearAll();
        for(auto* row:xml->getChildIterator()) if(row->hasTagName("row"))
            for(int s=0;s<16;++s) model.setStep(row->getIntAttribute("p",-1),row->getIntAttribute("n",-1),s,(row->getIntAttribute("bits")&(1<<s))!=0);
        model.selectPattern(xml->getIntAttribute("current",0));
    }
    meetstep::Pattern model;
};
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new MeetStepProcessor; }
