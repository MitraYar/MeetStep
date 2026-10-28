#include <juce_audio_devices/juce_audio_devices.h>
#include "Editor.h"
#include "LedFeedback.h"
#include <bitset>
#if JUCE_WINDOWS
#include <windows.h>
#endif
class Main : public juce::Component, private juce::MidiInputCallback, private juce::HighResolutionTimer,
             private juce::Timer, private juce::KeyListener {
public:
 meetstep::Pattern model; meetstep::Panel panel{model};
 juce::TextButton start{"Start"},stop{"Stop"},resume{"Continue"},settings{"Settings"},audition{"Audition: Off"};
 juce::Slider tempo; juce::Label status;
 explicit Main(bool testMode=false):testing(testMode){
  addAndMakeVisible(panel);
  for(auto* b:{&start,&stop,&resume,&settings,&audition}) addAndMakeVisible(*b);
  addAndMakeVisible(tempo);addAndMakeVisible(status);tempo.setRange(30,300,1);tempo.setValue(120);tempo.setTextBoxStyle(juce::Slider::TextBoxLeft,false,60,24);
  tempo.onValueChange=[this]{bpm.store(tempo.getValue());};
  start.onClick=[this]{transport(true,false);};stop.onClick=[this]{transport(false,false);};resume.onClick=[this]{transport(true,true);};
  audition.onClick=[this]{preview=!preview.load();audition.setButtonText(preview?"Audition: On":"Audition: Off");};settings.onClick=[this]{openSettings();};
  setWantsKeyboardFocus(true);setSize(960,760);if(!testing)restore();
  listenForShortcuts(*this);
  if(!testing){juce::HighResolutionTimer::startTimer(1);juce::Timer::startTimerHz(30);}
 }
 ~Main() override {juce::Timer::stopTimer();juce::HighResolutionTimer::stopTimer();leds.close();for(auto& input:inputs) input->stop();transport(false,false);if(!testing)save();}
 void resized() override {panel.setBounds(0,90,getWidth(),getHeight()-90);start.setBounds(16,12,70,30);stop.setBounds(92,12,70,30);resume.setBounds(168,12,90,30);settings.setBounds(264,12,90,30);audition.setBounds(360,12,130,30);tempo.setBounds(510,12,230,30);status.setBounds(16,48,getWidth()-32,30);}
 bool keyPressed(const juce::KeyPress& k) override {
  if(juce::Component::getNumCurrentlyModalComponents()>0)return false;
  for(auto* c=juce::Component::getCurrentlyFocusedComponent();c;c=c->getParentComponent())
   if(dynamic_cast<juce::TextEditor*>(c))return false;
  if(k.isKeyCode(juce::KeyPress::spaceKey)&&!k.getModifiers().isAnyModifierKeyDown()){
   if(!spaceDown){spaceDown=true;toggleTransport();}return true;
  }
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
#if MEETSTEP_TESTING
 static bool selfTest();
#endif
private:
 meetstep::LedFeedback leds;
 juce::String ledOutputId,ledInputId;
 bool testing=false,spaceDown=false,ledErrorShown=false;
 bool keyPressed(const juce::KeyPress& k,juce::Component*) override {return keyPressed(k);}
 bool keyStateChanged(bool,juce::Component*) override {
  if(!juce::KeyPress::isKeyCurrentlyDown(juce::KeyPress::spaceKey))spaceDown=false;
  return false;
 }
 void listenForShortcuts(juce::Component& component){
  if(dynamic_cast<juce::TextEditor*>(&component))return;
  component.addKeyListener(this);
  for(auto* child:component.getChildren())listenForShortcuts(*child);
 }
 void timerCallback() override {
  if(!juce::KeyPress::isKeyCurrentlyDown(juce::KeyPress::spaceKey))spaceDown=false;
  leds.update(meetstep::ledFrame(model));
  if(leds.hasFailed()&&!ledErrorShown){ledErrorShown=true;status.setText("LED ACK timeout: colour sending stopped. Check SMK ports, then Apply settings to reconnect.",juce::dontSendNotification);}
 }
 juce::CriticalSection lock;std::vector<std::unique_ptr<juce::MidiInput>> inputs;std::unique_ptr<juce::MidiOutput> output;
 std::atomic<bool> preview{false};std::atomic<double>bpm{120};bool running=false;int tick=0;double next=0;std::bitset<128> sounding,live;
#if MEETSTEP_TESTING
 std::function<void(const juce::MidiMessage&)> observeMidi;
#endif
 void send(const juce::MidiMessage& m){
#if MEETSTEP_TESTING
  if(observeMidi)observeMidi(m);
#endif
  if(output)output->sendMessageNow(m);
 }
 void silence(){for(int n=0;n<128;++n)if(sounding[n]||live[n])send(juce::MidiMessage::noteOff(1,n));sounding.reset();live.reset();}
 void transport(bool play,bool cont){const juce::ScopedLock guard(lock);silence();running=play;if(!play)panel.getGrid().playingStep=-1;if(play&&!cont)tick=0;next=juce::Time::getMillisecondCounterHiRes();send(play?(cont?juce::MidiMessage::midiContinue():juce::MidiMessage::midiStart()):juce::MidiMessage::midiStop());}
 void toggleTransport(){const juce::ScopedLock guard(lock);transport(!running,false);}
 void handleIncomingMidiMessage(juce::MidiInput*,const juce::MidiMessage& m) override {
  if(m.isSysEx()){leds.receive(m);return;}
  const juce::ScopedLock guard(lock);
  if(m.isNoteOn()){
   if(meetstep::isPlayStopPad(m.getChannel(),m.getNoteNumber(),m.getVelocity())){toggleTransport();return;}
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
  auto* content=new SettingsContent;content->setSize(520,310+int(ins.size())*28);
  std::vector<juce::ToggleButton*> checks;
  int y=12;for(auto d:ins){auto* b=new juce::ToggleButton(d.name);content->addAndMakeVisible(b);b->setBounds(12,y,490,26);y+=28;checks.push_back(b);for(auto& i:inputs)if(i->getIdentifier()==d.identifier)b->setToggleState(true,juce::dontSendNotification);}
  auto label=[content](const juce::String& text,int top){auto* l=new juce::Label({},text);content->addAndMakeVisible(l);l->setBounds(12,top,490,22);};
  label("Sequencer MIDI output (DAW)",y);
  auto* out=new juce::ComboBox;content->addAndMakeVisible(out);out->setBounds(12,y+22,490,30);out->addItem("No MIDI output",1);int id=2;for(auto d:outs)out->addItem(d.name,id++);out->setSelectedId(1);if(output)for(int i=0;i<outs.size();++i)if(outs[i].identifier==output->getIdentifier())out->setSelectedId(i+2);
  label("Pad colour MIDI output (SMK)",y+60);
  auto* colourOut=new juce::ComboBox;content->addAndMakeVisible(colourOut);colourOut->setBounds(12,y+82,490,30);colourOut->addItem("Colours off",1);id=2;for(auto d:outs)colourOut->addItem(d.name,id++);colourOut->setSelectedId(1,juce::dontSendNotification);for(int i=0;i<outs.size();++i)if(outs[i].identifier==ledOutputId)colourOut->setSelectedId(i+2,juce::dontSendNotification);
  label("SMK MIDI input for colour replies (Maximum mode)",y+120);
  auto* colourIn=new juce::ComboBox;content->addAndMakeVisible(colourIn);colourIn->setBounds(12,y+142,490,30);colourIn->addItem("Choose SMK input",1);id=2;for(auto d:ins)colourIn->addItem(d.name,id++);colourIn->setSelectedId(1,juce::dontSendNotification);for(int i=0;i<ins.size();++i)if(ins[i].identifier==ledInputId)colourIn->setSelectedId(i+2,juce::dontSendNotification);
  colourOut->onChange=[colourOut,colourIn,ins,outs]{if(colourOut->getSelectedId()>1){const auto& name=outs[colourOut->getSelectedId()-2].name;for(int i=0;i<ins.size();++i)if(ins[i].name==name){colourIn->setSelectedId(i+2);return;}}};
  label("Preset 1 (index 0). Pad 25 / Space: Play / Stop.",y+182);
  auto* apply=new juce::TextButton("Apply");auto* close=new juce::TextButton("Close");content->addAndMakeVisible(apply);content->addAndMakeVisible(close);apply->setBounds(280,y+222,100,30);close->setBounds(392,y+222,100,30);
  juce::DialogWindow::LaunchOptions options;options.content.setOwned(content);options.dialogTitle="MIDI settings";options.dialogBackgroundColour=juce::Colour(0xff242b36);options.useNativeTitleBar=true;options.resizable=false;
  auto* dialog=options.launchAsync();juce::Component::SafePointer<juce::DialogWindow> window(dialog);
  close->onClick=[window]{if(window)window->exitModalState(0);};
  apply->onClick=[this,checks,ins,outs,out,colourOut,colourIn]{
   const auto selectedOut=out->getSelectedId()>1?outs[out->getSelectedId()-2].identifier:juce::String();
   const auto selectedLed=colourOut->getSelectedId()>1?outs[colourOut->getSelectedId()-2].identifier:juce::String();
   if(selectedLed.isNotEmpty()&&(selectedLed==selectedOut||colourIn->getSelectedId()<=1)){
    status.setText("Choose a separate SMK colour output and its SMK reply input; DAW output must be different.",juce::dontSendNotification);return;
   }
   leds.close();ledErrorShown=false;ledOutputId.clear();ledInputId.clear();
   for(auto& i:inputs)i->stop();inputs.clear();transport(false,false);
   juce::String error;
   {const juce::ScopedLock guard(lock);output.reset();if(out->getSelectedId()>1){output=juce::MidiOutput::openDevice(outs[out->getSelectedId()-2].identifier);if(!output)error="Cannot open output. ";}}
   for(int i=0;i<ins.size();++i)if(checks[i]->getToggleState()){auto input=juce::MidiInput::openDevice(ins[i].identifier,this);if(input){input->start();inputs.push_back(std::move(input));}else error+="Cannot open "+ins[i].name+". ";}
   if(selectedLed.isNotEmpty()){
    const auto inputId=ins[colourIn->getSelectedId()-2].identifier;
    bool shared=false;for(auto& input:inputs)if(input->getIdentifier()==inputId)shared=true;
    const auto ledError=leds.open(selectedLed,inputId,shared,meetstep::ledFrame(model));
    if(ledError.isNotEmpty())error+=ledError;else{ledOutputId=selectedLed;ledInputId=inputId;}
   }
   status.setText(error.isNotEmpty()?error:juce::String(inputs.size())+" inputs | "+(output?output->getName():"No output")+(ledOutputId.isNotEmpty()?" | Colours: Maximum":" | Colours off"),juce::dontSendNotification);
  };
 }
};
#if MEETSTEP_TESTING
#include "../tests/StandaloneChecks.h"
#endif
class App : public juce::JUCEApplication {
public:
 const juce::String getApplicationName() override{return "MeetStep";}const juce::String getApplicationVersion() override{return "0.2.4";}
 class Window:public juce::DocumentWindow{public:Window():DocumentWindow("MeetStep Standalone",juce::Colours::black,allButtons){setUsingNativeTitleBar(true);setContentOwned(new Main,true);centreWithSize(960,760);setVisible(true);}void closeButtonPressed() override{juce::JUCEApplication::getInstance()->systemRequestedQuit();}};
 std::unique_ptr<Window> window;void initialise(const juce::String& args)override{
#if MEETSTEP_TESTING
  if(args=="--self-test"){setApplicationReturnValue(Main::selfTest()?0:1);quit();return;}
#endif
  window=std::make_unique<Window>();
 }void shutdown()override{window.reset();}
};
START_JUCE_APPLICATION(App)
