#include <juce_audio_devices/juce_audio_devices.h>
#include "Editor.h"
#include <bitset>
#if JUCE_WINDOWS
#include <windows.h>
#endif
class Main : public juce::Component, private juce::MidiInputCallback, private juce::HighResolutionTimer {
public:
 meetstep::Pattern model; meetstep::Panel panel{model};
 juce::TextButton start{"Start"},stop{"Stop"},resume{"Continue"},settings{"Settings"},audition{"Audition: Off"};
 juce::Slider tempo; juce::Label status;
 Main(){
  addAndMakeVisible(panel);
  for(auto* b:{&start,&stop,&resume,&settings,&audition}) addAndMakeVisible(*b);
  addAndMakeVisible(tempo);addAndMakeVisible(status);tempo.setRange(30,240,1);tempo.setValue(120);tempo.setTextBoxStyle(juce::Slider::TextBoxLeft,false,60,24);
  tempo.onValueChange=[this]{bpm.store(tempo.getValue());};
  start.onClick=[this]{transport(true,false);};stop.onClick=[this]{transport(false,false);};resume.onClick=[this]{transport(true,true);};
  audition.onClick=[this]{preview=!preview.load();audition.setButtonText(preview?"Audition: On":"Audition: Off");};settings.onClick=[this]{openSettings();};
  setWantsKeyboardFocus(true);setSize(960,760);restore();startTimer(1);
 }
 ~Main() override {save();stopTimer();for(auto& input:inputs) input->stop();transport(false,false);}
 void resized() override {panel.setBounds(0,90,getWidth(),getHeight()-90);start.setBounds(16,12,70,30);stop.setBounds(92,12,70,30);resume.setBounds(168,12,90,30);settings.setBounds(264,12,90,30);audition.setBounds(360,12,130,30);tempo.setBounds(510,12,230,30);status.setBounds(16,48,getWidth()-32,30);}
 bool keyStateChanged(bool) override {
  if(!juce::KeyPress::isKeyCurrentlyDown(juce::KeyPress::spaceKey)) spaceHeld=false;
  return false;
 }
 bool keyPressed(const juce::KeyPress& k) override {
  if(k.getKeyCode()==juce::KeyPress::spaceKey){if(!spaceHeld){spaceHeld=true;togglePlayback();}return true;}
  auto c=k.getTextCharacter();
  bool slash=c=='/';
#if JUCE_WINDOWS
  slash=slash || ((GetAsyncKeyState(VK_OEM_2)&0x8000)!=0);
#endif
  if(slash){audition.onClick();return true;}
  if(c==','||c=='<'||c==0x0431){page(-16);return true;}
  if(c=='.'||c=='>'||c==0x044e){page(16);return true;}
  return false;
 }
 void page(int d){auto& g=panel.getGrid();g.baseNote=juce::jlimit(0,112,g.baseNote+d);g.repaint();}
private:
 juce::CriticalSection lock;std::vector<std::unique_ptr<juce::MidiInput>> inputs;std::unique_ptr<juce::MidiOutput> output;
 std::atomic<bool> preview{false};std::atomic<double>bpm{120};bool spaceHeld=false;bool running=false;int tick=0;double next=0;std::bitset<128> sounding,live;
 void send(const juce::MidiMessage& m){if(output)output->sendMessageNow(m);}
 void silence(){for(int n=0;n<128;++n)if(sounding[n]||live[n])send(juce::MidiMessage::noteOff(1,n));sounding.reset();live.reset();}
 void transport(bool play,bool cont){const juce::ScopedLock guard(lock);silence();running=play;if(!play)panel.getGrid().playingStep=-1;if(play&&!cont)tick=0;next=juce::Time::getMillisecondCounterHiRes();send(play?(cont?juce::MidiMessage::midiContinue():juce::MidiMessage::midiStart()):juce::MidiMessage::midiStop());}
 void togglePlayback(){const juce::ScopedLock guard(lock);transport(!running,true);}
 void handleIncomingMidiMessage(juce::MidiInput*,const juce::MidiMessage& m) override {
  const juce::ScopedLock guard(lock);
  if((m.getChannel()==10||m.getChannel()==11)&&m.getNoteNumber()==63&&(m.isNoteOn()||m.isNoteOff())){
   if(m.isNoteOn()) togglePlayback();
   return;
  }
  if(m.isNoteOn()){
   model.noteOn(m.getChannel(),m.getNoteNumber(),m.getVelocity());
   if(m.getChannel()!=10){
    const int n=m.getNoteNumber();juce::Component::SafePointer<Main> safe(this);
    juce::MessageManager::callAsync([safe,n]{if(safe){auto& g=safe->panel.getGrid();if(n<g.baseNote||n>g.baseNote+15)g.baseNote=juce::jlimit(0,112,36+int(std::floor((n-36)/16.0))*16);g.repaint();}});
    if(preview){send(juce::MidiMessage::noteOn(1,n,m.getVelocity()));live.set(n);}
   }
  }else if(m.isNoteOff()&&m.getChannel()!=10&&live[m.getNoteNumber()]){send(juce::MidiMessage::noteOff(1,m.getNoteNumber()));live.reset(m.getNoteNumber());}
 }
 void hiResTimerCallback() override {
  const juce::ScopedLock guard(lock);if(!running)return;
  const double now=juce::Time::getMillisecondCounterHiRes();if(now<next)return;
  if(now-next>100){silence();next=now;}
  send(juce::MidiMessage::midiClock());
  if(tick%6==0){panel.getGrid().playingStep=(tick/6)%16;for(int n=0;n<128;++n)if(sounding[n])send(juce::MidiMessage::noteOff(1,n));sounding.reset();
   for(int n=0;n<128;++n)if(model.enabled(n,(tick/6)%16)){send(juce::MidiMessage::noteOn(1,n,(juce::uint8)100));sounding.set(n);}}
  tick=(tick+1)%96;next+=60000.0/(bpm.load()*24.0);
 }
 juce::File stateFile(){return juce::File::getSpecialLocation(juce::File::userApplicationDataDirectory).getChildFile("MeetStep/patterns.xml");}
 void save(){juce::XmlElement root("MeetStep");root.setAttribute("current",model.currentPattern());root.setAttribute("bpm",bpm.load());
  for(int p=0;p<6;++p)for(int n=0;n<128;++n){int bits=0;for(int s=0;s<16;++s)if(model.enabled(p,n,s))bits|=1<<s;if(bits){auto* r=root.createNewChildElement("row");r->setAttribute("p",p);r->setAttribute("n",n);r->setAttribute("bits",bits);}}
  auto f=stateFile();f.getParentDirectory().createDirectory();root.writeTo(f);}
 void restore(){auto root=juce::XmlDocument::parse(stateFile());if(!root||!root->hasTagName("MeetStep"))return;
  for(auto* r:root->getChildIterator())for(int s=0;s<16;++s)model.setStep(r->getIntAttribute("p",-1),r->getIntAttribute("n",-1),s,(r->getIntAttribute("bits")&(1<<s))!=0);
  model.selectPattern(root->getIntAttribute("current"));tempo.setValue(root->getDoubleAttribute("bpm",120));}
 void openSettings(){
  auto ins=juce::MidiInput::getAvailableDevices();auto outs=juce::MidiOutput::getAvailableDevices();
  struct SettingsContent:juce::Component{~SettingsContent() override{deleteAllChildren();}};
  auto* content=new SettingsContent;content->setSize(520,150+int(ins.size())*28);
  std::vector<juce::ToggleButton*> checks;
  int y=12;for(auto d:ins){auto* b=new juce::ToggleButton(d.name);content->addAndMakeVisible(b);b->setBounds(12,y,490,26);y+=28;checks.push_back(b);for(auto& i:inputs)if(i->getIdentifier()==d.identifier)b->setToggleState(true,juce::dontSendNotification);}
  auto* out=new juce::ComboBox;content->addAndMakeVisible(out);out->setBounds(12,y,490,30);out->addItem("No MIDI output",1);int id=2;for(auto d:outs)out->addItem(d.name,id++);out->setSelectedId(1);if(output)for(int i=0;i<outs.size();++i)if(outs[i].identifier==output->getIdentifier())out->setSelectedId(i+2);
  auto* apply=new juce::TextButton("Apply");auto* close=new juce::TextButton("Close");content->addAndMakeVisible(apply);content->addAndMakeVisible(close);apply->setBounds(280,y+44,100,30);close->setBounds(392,y+44,100,30);
  juce::DialogWindow::LaunchOptions options;options.content.setOwned(content);options.dialogTitle="MIDI settings";options.dialogBackgroundColour=juce::Colour(0xff242b36);options.useNativeTitleBar=true;options.resizable=false;
  auto* dialog=options.launchAsync();juce::Component::SafePointer<juce::DialogWindow> window(dialog);
  close->onClick=[window]{if(window)window->exitModalState(0);};
  apply->onClick=[this,checks,ins,outs,out]{
   for(auto& i:inputs)i->stop();inputs.clear();transport(false,false);
   juce::String error;
   {const juce::ScopedLock guard(lock);output.reset();if(out->getSelectedId()>1){output=juce::MidiOutput::openDevice(outs[out->getSelectedId()-2].identifier);if(!output)error="Cannot open output. ";}}
   for(int i=0;i<ins.size();++i)if(checks[i]->getToggleState()){auto input=juce::MidiInput::openDevice(ins[i].identifier,this);if(input){input->start();inputs.push_back(std::move(input));}else error+="Cannot open "+ins[i].name+". ";}
   status.setText(error.isNotEmpty()?error:juce::String(inputs.size())+" inputs | "+(output?output->getName():"No output"),juce::dontSendNotification);
  };
 }
};
class App : public juce::JUCEApplication {
public:
 const juce::String getApplicationName() override{return "MeetStep";}const juce::String getApplicationVersion() override{return "0.2.1";}
 class Window:public juce::DocumentWindow{public:Window():DocumentWindow("MeetStep Standalone",juce::Colours::black,allButtons){setUsingNativeTitleBar(true);setContentOwned(new Main,true);centreWithSize(960,760);setVisible(true);}void closeButtonPressed() override{juce::JUCEApplication::getInstance()->systemRequestedQuit();}};
 std::unique_ptr<Window> window;void initialise(const juce::String&)override{window=std::make_unique<Window>();}void shutdown()override{window.reset();}
};
START_JUCE_APPLICATION(App)
