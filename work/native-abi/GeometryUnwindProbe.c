#include <stdio.h>
#include "GeometryLOD.h"
static volatile LONG gate;
int main(void) {
    const wchar_t *path=L"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Ratchet & Clank - Rift Apart\\RiftApart.exe";
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,0,NULL);
    if(file==INVALID_HANDLE_VALUE)return 1;
    HANDLE mapping=CreateFileMappingW(file,NULL,PAGE_READONLY|SEC_IMAGE,0,0,NULL);
    if(!mapping)return 2;
    unsigned char *image=MapViewOfFile(mapping,FILE_MAP_READ,0,0,0);
    if(!image)return 3;
    uintptr_t base=(uintptr_t)image;
    IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER*)image;
    IMAGE_NT_HEADERS64 *nt=(IMAGE_NT_HEADERS64*)(image+dos->e_lfanew);
    IMAGE_DATA_DIRECTORY dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXCEPTION];
    RUNTIME_FUNCTION *all=(RUNTIME_FUNCTION*)(image+dir.VirtualAddress);
    RUNTIME_FUNCTION original[2]={0};DWORD sites[2]={0x111a860,0x111a9e8};
    for(unsigned i=0;i<dir.Size/sizeof(RUNTIME_FUNCTION);i++)
        for(int j=0;j<2;j++)if(all[i].BeginAddress<=sites[j] && sites[j]<all[i].EndAddress)original[j]=all[i];
    if(!original[0].BeginAddress || !original[1].BeginAddress)return 4;
    GeometryPatch p={0};
    if(!geometry_prepare(&p,base,base+nt->OptionalHeader.SizeOfImage,image+sites[0],image+sites[1],&gate,original))return 5;
    uint64_t stack[256];for(int i=0;i<256;i++)stack[i]=0x12340000+i;
    uintptr_t sp=(uintptr_t)&stack[32];
    for(int index=0;index<2;index++) {
        CONTEXT seed;memset(&seed,0x35,sizeof(seed));seed.ContextFlags=CONTEXT_FULL;seed.Rsp=sp;
        CONTEXT native=seed;native.Rip=base+sites[index];
        PVOID handler=NULL;DWORD64 establisher=0;
        RtlVirtualUnwind(UNW_FLAG_NHANDLER,base,native.Rip,&original[index],&native,&handler,&establisher,NULL);
        const int boundaries[]={0,2,12,15,17,19,26,36};
        for(unsigned point=0;point<sizeof(boundaries)/sizeof(boundaries[0]);point++) {
            int offset=boundaries[point];
            CONTEXT relay=seed;relay.Rip=(DWORD64)(p.sites[index].relay+offset);
            DWORD64 dynamic_base=0;RUNTIME_FUNCTION *entry=RtlLookupFunctionEntry(relay.Rip,&dynamic_base,NULL);
            if(entry!=&p.table[index] || dynamic_base!=base)return 6;
            RtlVirtualUnwind(UNW_FLAG_NHANDLER,base,relay.Rip,entry,&relay,&handler,&establisher,NULL);
            if(memcmp(&native,&relay,sizeof(native))) {
                printf("Mismatch selector %d relay offset %d\n",index,offset);return 7;
            }
        }
    }
    puts("PASS: both relay unwind chains exactly match the real game's complete GPR/XMM/stack contexts at all eight instruction boundaries; executable mapped read-only and never patched.");
    return 0;
}
