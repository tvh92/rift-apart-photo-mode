
#include <stdint.h>
#include <stdio.h>
#include <string.h>
uint64_t observed_registers[7],observed_flags,callback_alignment,original_alignment;
unsigned char observed_xmm[96];
const unsigned char input_xmm[16]={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16};
void *original_free,*original_motion,*hid_targets[44];
void *original_photo_destroy,*original_photo_cleanup;
extern void TestOriginal(void);
extern int TestFree(void),TestMotion(void),TestForward(void);
extern int TestPhotoDestroy(void),TestPhotoCleanup(void);
int main(void) {
 original_free=original_motion=hid_targets[0]=(void*)TestOriginal;
 original_photo_destroy=original_photo_cleanup=(void*)TestOriginal;
 int (*tests[])(void)={TestFree,TestMotion,TestForward,TestPhotoDestroy,TestPhotoCleanup};
 for(int t=0;t<5;t++) {
  if(tests[t]()!=1234 || callback_alignment!=8 || original_alignment!=8 || !(observed_flags&1))return 1;
  for(int i=0;i<7;i++)if(observed_registers[i]!=(uint64_t)(0x1111*(i+1)))return 2;
  for(int i=0;i<6;i++)if(memcmp(observed_xmm+16*i,input_xmm,16))return 3;
 }
 puts("PASS: camera/Photo teardown hooks and HID forwarding preserve GPRs, six XMM registers, flags, arguments, alignment and callback shadow space.");return 0;
}
