#pragma once
#include "LedFeedback.h"

// Runs through the packaged --led-self-test entry point without MIDI hardware.
inline bool testLedWorker() {
    using namespace std::chrono_literals;
    auto until=[](auto condition){
        const auto end=std::chrono::steady_clock::now()+1s;
        while(!condition()){
            if(std::chrono::steady_clock::now()>=end)return false;
            std::this_thread::sleep_for(1ms);
        }
        return true;
    };
    const unsigned char bytes[]={0xf0,0,0x32,1,8,0,0,0,0,0x7f,1,0xf7};
    const juce::MidiMessage ack(bytes,sizeof(bytes));
    meetstep::LedFeedback led;
    std::atomic<int> sends{0};
    // An echoed colour packet and a real ACK must not trigger more writes.
    led.start([&](const juce::MidiMessage& m){++sends;led.receive(m);led.receive(ack);},false,20ms);
    if(!until([&]{return sends.load()==16;}))return false;
    std::this_thread::sleep_for(40ms);
    if(sends!=16||led.hasFailed())return false;
    std::array<int,16> state{};state[7]=127;
    led.update(state);
    if(!until([&]{return sends.load()==17;}))return false;
    for(int i=0;i<20;++i)led.update(state);
    std::this_thread::sleep_for(40ms);
    if(sends!=17)return false;
    led.close();
    // Send-only also continues with no incoming MIDI at all.
    sends=0;led.start([&](const juce::MidiMessage&){++sends;},false,20ms);
    if(!until([&]{return sends.load()==16;}))return false;
    std::this_thread::sleep_for(40ms);
    if(led.hasFailed())return false;
    led.update(state);if(!until([&]{return sends.load()==17;}))return false;
    led.close();
    // ACK mode rejects echoed writes, stops on timeout, and never retries.
    sends=0;led.start([&](const juce::MidiMessage& m){++sends;led.receive(m);},true,20ms);
    if(!until([&]{return led.hasFailed();})||sends!=1)return false;
    led.update(state);std::this_thread::sleep_for(40ms);if(sends!=1)return false;
    led.close();if(led.hasFailed())return false;
    // Immediate ACKs work and closing an ACK wait does not wait for its timeout.
    sends=0;led.start([&](const juce::MidiMessage&){++sends;led.receive(ack);},true,100ms);
    if(!until([&]{return sends.load()==16;}))return false;
    led.close();
    sends=0;led.start([&](const juce::MidiMessage&){++sends;},true,2s);
    if(!until([&]{return sends.load()==1;}))return false;
    const auto before=std::chrono::steady_clock::now();led.close();
    return std::chrono::steady_clock::now()-before<500ms;
}
