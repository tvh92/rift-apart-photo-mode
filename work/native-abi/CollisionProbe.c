#define HID_EXPORT_COUNT 44
#include "../../outputs/camera-native/CameraBoost.c"
int main(void) {
    static const unsigned char expected[9]={0xe8,0x44,0xaa,0x75,0xff,0x84,0xc0,0x74,0x3b};
    unsigned char *p=VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
    if(!p)return 1;
    memcpy(p,expected,9);
    p[0]=0x90;
    if(prepare_collision_bypass(p) || collision_branch || memcmp(p+1,expected+1,8))return 2;
    memcpy(p,expected,9);
    if(!prepare_collision_bypass(p) || !collision_changed || p[7]!=0xeb)return 3;
    for(int i=0;i<9;i++)if(i!=7 && p[i]!=expected[i])return 4;
    MEMORY_BASIC_INFORMATION info;
    if(!VirtualQuery(p,&info,sizeof(info)) || info.Protect!=PAGE_READWRITE)return 5;
    if(!set_collision_bypass(FALSE) || collision_changed || memcmp(p,expected,9))return 6;
    if(!set_collision_bypass(TRUE))return 7;
    p[7]=0x75;
    if(set_collision_bypass(FALSE) || p[7]!=0x75)return 8;
    p[7]=0xeb;
    if(!set_collision_bypass(FALSE) || memcmp(p,expected,9))return 9;
    VirtualFree(p,0,MEM_RELEASE);
    puts("PASS: exact collision window guard, one-byte bypass, original response restore, original page protection, and refusal to overwrite a changed branch.");
    return 0;
}
