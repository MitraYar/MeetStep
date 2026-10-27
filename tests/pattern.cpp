#include "Pattern.h"
#include <cstdlib>
#include <iostream>
void check(bool ok) { if (!ok) { std::cerr << "FAILED\n"; std::exit(1); } }
int main() {
    meetstep::Pattern p;
    p.noteOn(10,40,100);
    check(p.selectedNote() == -1);
    p.noteOn(1,36,100);
    for (int i=0;i<16;++i) {
        p.noteOn(10,meetstep::Pattern::bank1[i],100);
        check(p.enabled(36,i));
    }
    p.noteOn(10,40,0); check(p.enabled(36,0));
    p.noteOn(10,40,100); check(!p.enabled(36,0));
    p.noteOn(2,38,100); check(!p.enabled(38,1));
    p.noteOn(10,41,100); check(p.enabled(38,1));
    check(p.enabled(36,1));
    for (int n: meetstep::Pattern::bank2) p.noteOn(10,n,100);
    for (int i=0;i<16;++i) check(p.enabled(38,i) == (i==1));
    p.noteOn(0,60,100); p.noteOn(17,60,100); p.noteOn(1,128,100);
    check(p.selectedNote()==38);
    for (int ch=1;ch<=16;++ch) if(ch!=10) {
        p.noteOn(ch,60+ch,100); check(p.selectedNote()==60+ch);
    }
    p.selectPattern(1); check(!p.enabled(36,1));
    p.setStep(1,36,2,true); p.selectPattern(0); check(p.enabled(36,1));
    check(p.enabled(36,2)); // Original pattern still has step 3.
    p.clearCurrent(); check(!p.enabled(36,1)); check(p.enabled(1,36,2));
    p.selectPattern(5);
    meetstep::GridStroke stroke(p);
    stroke.begin(36,0,true); stroke.drag(15); stroke.end();
    for(int s=0;s<16;++s) check(p.enabled(36,s));
    check(!p.enabled(37,0));
    stroke.begin(36,15,false); stroke.drag(0); stroke.end();
    for(int s=0;s<16;++s) check(!p.enabled(36,s));
    stroke.begin(40,3,true); stroke.drag(3); stroke.end(); check(p.enabled(40,3));
    stroke.drag(7); check(!p.enabled(40,7));
    stroke.begin(40,3,true); p.selectPattern(4); stroke.drag(5); stroke.end();
    check(p.enabled(5,40,5)); check(!p.enabled(4,40,5));
    p.selectPattern(-1); p.selectPattern(6); check(p.currentPattern()==4);
    p.setStep(-1,36,1,true); p.setStep(0,128,1,true); p.setStep(0,36,16,true);
    p.clearAll();
    for(int b=0;b<6;++b) for(int n=0;n<128;++n) for(int s=0;s<16;++s)
        check(!p.enabled(b,n,s));
    std::cout << "Controller mapping and pattern tests passed\n";
}
