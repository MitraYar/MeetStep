#pragma once
#include <juce_audio_devices/juce_audio_devices.h>
#include <array>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <functional>
namespace meetstep {
inline std::array<int,4> ledColour(int velocity) {
    const int v=juce::jlimit(0,127,velocity);
    return {190*v/127,220*v/127,255*v/127,v?255:0};
}
inline juce::MidiMessage ledPacket(int pad,int velocity) {
    const unsigned address=0x11b+pad*0x4a;
    std::vector<unsigned char> data{5};
    for(int i=0;i<4;++i)data.push_back((address>>(8*i))&255);
    data.insert(data.end(),{4,0,0});
    for(auto c:ledColour(velocity))data.push_back((unsigned char)c);
    std::vector<unsigned char> raw{0,0x59,0x22,12,0,0};
    unsigned sum=0;for(auto b:data){raw.push_back(b);sum+=b;}raw.push_back((~sum)&255);
    std::vector<unsigned char> encoded;unsigned acc=0;int bits=0;
    for(auto b:raw){acc|=unsigned(b)<<bits;bits+=8;while(bits>=7){encoded.push_back(acc&127);acc>>=7;bits-=7;}}
    if(bits)encoded.push_back(acc&127);
    return juce::MidiMessage::createSysExMessage(encoded.data(),(int)encoded.size());
}
// Dedicated output worker; input SysEx is never echoed. ACK is optional.
class LedFeedback : private juce::MidiInputCallback {
public:
    ~LedFeedback(){close();}
    juce::String open(const juce::String& out,const juce::String& in,bool sharedInput=false,bool requireAck=false){
        close();if(out.isEmpty())return {};
        output=juce::MidiOutput::openDevice(out);
        if(requireAck&&!sharedInput)input=juce::MidiInput::openDevice(in,this);
        if(!output||(requireAck&&!sharedInput&&!input)){close();return "Cannot open LED feedback device / ACK input";}
        if(input)input->start();
        start([this](const juce::MidiMessage& message){output->sendMessageNow(message);},requireAck);return {};
    }
    // The same worker can use a fake MIDI sink in regression tests.
    void start(std::function<void(const juce::MidiMessage&)> sink,bool requireAck,
               std::chrono::milliseconds timeout=std::chrono::seconds(2)){
        stopWorker();
        {std::lock_guard<std::mutex> g(mutex);quit=false;failed=false;ack=false;waiting=false;
         waitForAck=requireAck;ackTimeout=timeout;send=std::move(sink);desired.fill(0);sent.fill(-1);}
        worker=std::thread([this]{run();});
    }
    void close(){
        stopWorker();if(input)input->stop();input.reset();output.reset();
    }
    void stopWorker(){
        {std::lock_guard<std::mutex> g(mutex);quit=true;}wake.notify_all();
        if(worker.joinable())worker.join();
        {std::lock_guard<std::mutex> g(mutex);waiting=false;failed=false;}
    }
    void update(const std::array<int,16>& values){std::lock_guard<std::mutex> g(mutex);desired=values;wake.notify_all();}
    bool hasFailed(){std::lock_guard<std::mutex> g(mutex);return failed;}
    void receive(const juce::MidiMessage& m){handleIncomingMidiMessage(nullptr,m);}
private:
    std::unique_ptr<juce::MidiInput> input;std::unique_ptr<juce::MidiOutput> output;
    std::mutex mutex;std::condition_variable wake;std::thread worker;
    std::array<int,16> desired{},sent{};bool quit=true,failed=false,ack=false,waiting=false,waitForAck=false;
    std::function<void(const juce::MidiMessage&)> send;
    std::chrono::milliseconds ackTimeout{2000};
    void handleIncomingMidiMessage(juce::MidiInput*,const juce::MidiMessage& m) override {
        static const unsigned char expected[]={0xf0,0,0x32,1,8,0,0,0,0,0x7f,1,0xf7};
        if(m.getRawDataSize()!=sizeof(expected)||std::memcmp(m.getRawData(),expected,sizeof(expected)))return;
        std::lock_guard<std::mutex> g(mutex);if(waiting){ack=true;wake.notify_all();}
    }
    void run(){
        std::unique_lock<std::mutex> g(mutex);
        while(!quit){
            int pad=-1;for(int i=0;i<16;++i)if(sent[i]!=desired[i]){pad=i;break;}
            if(pad<0){wake.wait(g);continue;}
            const int value=desired[pad];ack=false;waiting=waitForAck;
            g.unlock();send(ledPacket(pad,value));g.lock();
            if(waitForAck&&!wake.wait_for(g,ackTimeout,[this]{return ack||quit;})){
                waiting=false;failed=true;return; // no retries after uncertain delivery
            }
            waiting=false;if(quit)return;sent[pad]=value;
        }
    }
};
}
