#include <AudioToolbox/AudioToolbox.h>
#include <CoreFoundation/CoreFoundation.h>
#include <mach-o/dyld.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void require(OSStatus s, const char *stage) {
    if (s != noErr) { fprintf(stderr,"%s OSStatus=%d\n",stage,(int)s); exit(2); }
}
static OSType fourcc(const char *s) {
    if (strlen(s) != 4) { fprintf(stderr,"fourcc requires four bytes\n"); exit(2); }
    return ((UInt32)(unsigned char)s[0]<<24)|((UInt32)(unsigned char)s[1]<<16)|((UInt32)(unsigned char)s[2]<<8)|(unsigned char)s[3];
}
static void cftext(CFStringRef s,char *dst, size_t n) {
    if (!s || !CFStringGetCString(s,dst,n,kCFStringEncodingUTF8)) snprintf(dst,n,"?");
}
typedef struct { float *input; UInt32 frames; UInt32 offset; } Source;
static OSStatus supply(void *ctx, AudioUnitRenderActionFlags *flags,const AudioTimeStamp *ts,
                       UInt32 bus,UInt32 count,AudioBufferList *io) {
    Source *s=(Source *)ctx;
    if(io->mNumberBuffers!=2)return kAudio_ParamError;
    for (UInt32 b=0;b<io->mNumberBuffers;b++) {
        float *dst=(float *)io->mBuffers[b].mData;
        if (!dst) return kAudio_ParamError;
        for (UInt32 i=0;i<count;i++) {
            UInt32 frame=s->offset+i;
            dst[i]=frame<s->frames ? s->input[2*frame+b] : 0.0f;
        }
        io->mBuffers[b].mDataByteSize=count*sizeof(float);
    }
    return noErr;
}
int main(int argc,char **argv) {
    if (argc<5) { fprintf(stderr,"usage: au_probe type subtype maker info | render input.f32 output.f32 bypass [parameter=value ...]\n");return 2; }
    AudioComponentDescription desc={fourcc(argv[1]),fourcc(argv[2]),fourcc(argv[3]),0,0};
    AudioComponent comp=AudioComponentFindNext(NULL,&desc);
    if (!comp) { fprintf(stderr,"COMPONENT_NOT_FOUND\n");return 2; }
    AudioUnit unit=NULL; require(AudioComponentInstanceNew(comp,&unit),"instantiate");
    CFStringRef name=NULL; require(AudioComponentCopyName(comp,&name),"component_name");
    char text[1024];cftext(name,text,sizeof(text));printf("COMPONENT\t%s\n",text);CFRelease(name);
    UInt32 version=0;require(AudioComponentGetVersion(comp,&version),"version");printf("VERSION\t%u\n",version);
    UInt32 size=0;require(AudioUnitGetPropertyInfo(unit,kAudioUnitProperty_ParameterList,kAudioUnitScope_Global,0,&size,NULL),"parameter_list_size");
    AudioUnitParameterID *ids=calloc(size?size:1,1);
    if (size) require(AudioUnitGetProperty(unit,kAudioUnitProperty_ParameterList,kAudioUnitScope_Global,0,ids,&size),"parameter_list");
    for (UInt32 i=0;i<size/sizeof(*ids);i++) {
        AudioUnitParameterInfo info;UInt32 n=sizeof(info);require(AudioUnitGetProperty(unit,kAudioUnitProperty_ParameterInfo,kAudioUnitScope_Global,ids[i],&info,&n),"parameter_info");
        if (info.flags&kAudioUnitParameterFlag_HasCFNameString) cftext(info.cfNameString,text,sizeof(text)); else snprintf(text,sizeof(text),"%s",info.name);
        AudioUnitParameterValue value=0;OSStatus got=AudioUnitGetParameter(unit,ids[i],kAudioUnitScope_Global,0,&value);
        printf("PARAM\t%u\t%s\t%.9g\t%.9g\t%.9g\t%.9g\t%u\t%d\n",ids[i],text,info.minValue,info.maxValue,info.defaultValue,value,info.unit,(int)got);
        if ((info.flags&kAudioUnitParameterFlag_CFNameRelease)&&info.cfNameString) CFRelease(info.cfNameString);
    }
    free(ids);
    if (!strcmp(argv[4],"render")) {
        if (argc<8) return 2;
        FILE *in=fopen(argv[5],"rb");if (!in) return 2;
        fseek(in,0,SEEK_END);long bytes=ftell(in);rewind(in);
        if (bytes<=0||bytes%8||bytes>80000000) return 2;
        Source src={calloc((size_t)bytes,1),(UInt32)(bytes/8),0};
        if (fread(src.input,1,bytes,in)!=(size_t)bytes) return 2;fclose(in);
        AudioStreamBasicDescription fmt={48000,kAudioFormatLinearPCM,
            kAudioFormatFlagIsFloat|kAudioFormatFlagIsPacked|kAudioFormatFlagIsNonInterleaved,
            4,1,4,2,32,0};
        require(AudioUnitSetProperty(unit,kAudioUnitProperty_StreamFormat,kAudioUnitScope_Input,0,&fmt,sizeof(fmt)),"input_format");
        require(AudioUnitSetProperty(unit,kAudioUnitProperty_StreamFormat,kAudioUnitScope_Output,0,&fmt,sizeof(fmt)),"output_format");
        UInt32 block=256;require(AudioUnitSetProperty(unit,kAudioUnitProperty_MaximumFramesPerSlice,kAudioUnitScope_Global,0,&block,sizeof(block)),"block_size");
        AURenderCallbackStruct cb={supply,&src};require(AudioUnitSetProperty(unit,kAudioUnitProperty_SetRenderCallback,kAudioUnitScope_Input,0,&cb,sizeof(cb)),"input_callback");
        UInt32 offline=1;OSStatus off=AudioUnitSetProperty(unit,kAudioUnitProperty_OfflineRender,kAudioUnitScope_Global,0,&offline,sizeof(offline));printf("OFFLINE_STATUS\t%d\n",(int)off);
        for (int i=8;i<argc;i++) if (!strncmp(argv[i],"--state=",8)) {
            FILE *f=fopen(argv[i]+8,"rb");if(!f)return 2;
            fseek(f,0,SEEK_END);long len=ftell(f);rewind(f);UInt8 *raw=malloc(len);
            if(fread(raw,1,len,f)!=(size_t)len)return 2;fclose(f);
            CFDataRef data=CFDataCreate(NULL,raw,len);free(raw);
            CFPropertyListRef state=CFPropertyListCreateWithData(NULL,data,kCFPropertyListImmutable,NULL,NULL);
            if(!state)return 2;
            require(AudioUnitSetProperty(unit,kAudioUnitProperty_ClassInfo,kAudioUnitScope_Global,0,&state,sizeof(state)),"restore_state");
            CFRelease(state);CFRelease(data);
        }
        require(AudioUnitInitialize(unit),"initialize");
        UInt32 bypass=(UInt32)atoi(argv[7]);require(AudioUnitSetProperty(unit,kAudioUnitProperty_BypassEffect,kAudioUnitScope_Global,0,&bypass,sizeof(bypass)),"bypass");
        UInt32 actual_bypass=0;UInt32 bypass_size=sizeof(actual_bypass);
        require(AudioUnitGetProperty(unit,kAudioUnitProperty_BypassEffect,kAudioUnitScope_Global,0,&actual_bypass,&bypass_size),"read_bypass");
        printf("BYPASS\t%u\n",actual_bypass);
        for (int i=8;i<argc;i++) {
            if(!strncmp(argv[i],"--state=",8))continue;
            char *end=NULL;unsigned long id=strtoul(argv[i],&end,10);if (!end||*end!='=') return 2;
            float val=strtof(end+1,&end);if (*end||!isfinite(val)) return 2;
            require(AudioUnitSetParameter(unit,(UInt32)id,kAudioUnitScope_Global,0,val,0),"set_parameter");
            AudioUnitParameterValue readback;require(AudioUnitGetParameter(unit,(UInt32)id,kAudioUnitScope_Global,0,&readback),"read_parameter");
            printf("SET\t%lu\t%.9g\t%.9g\n",id,val,readback);
            AudioUnitParameterStringFromValue label={(UInt32)id,&readback,NULL};UInt32 labelsize=sizeof(label);
            OSStatus labelstatus=AudioUnitGetProperty(unit,kAudioUnitProperty_ParameterStringFromValue,kAudioUnitScope_Global,0,&label,&labelsize);
            if(labelstatus==noErr&&label.outString){cftext(label.outString,text,sizeof(text));printf("LABEL\t%lu\t%s\n",id,text);CFRelease(label.outString);}

        }
        CFPropertyListRef state=NULL;UInt32 statesize=sizeof(state);
        require(AudioUnitGetProperty(unit,kAudioUnitProperty_ClassInfo,kAudioUnitScope_Global,0,&state,&statesize),"snapshot_state");
        CFDataRef statedata=CFPropertyListCreateData(NULL,state,kCFPropertyListXMLFormat_v1_0,0,NULL);
        if(!statedata)return 2;
        char statepath[4096];snprintf(statepath,sizeof(statepath),"%s.state.plist",argv[6]);
        FILE *statefile=fopen(statepath,"wb");if(!statefile)return 2;
        if(fwrite(CFDataGetBytePtr(statedata),1,CFDataGetLength(statedata),statefile)!=(size_t)CFDataGetLength(statedata))return 2;
        if(fclose(statefile))return 2;CFRelease(statedata);CFRelease(state);
        Float64 latency=0;UInt32 n=sizeof(latency);OSStatus lat=AudioUnitGetProperty(unit,kAudioUnitProperty_Latency,kAudioUnitScope_Global,0,&latency,&n);printf("LATENCY\t%.9g\t%d\n",latency,(int)lat);
        struct { UInt32 count; AudioBuffer buffers[2]; } buffers={2,{{1,block*4,calloc(block,4)},{1,block*4,calloc(block,4)}}};
        FILE *out=fopen(argv[6],"wb");if (!out) return 2;
        float frame[2];
        for (UInt32 pos=0;pos<src.frames;pos+=block) {
            UInt32 count=(src.frames-pos<block)?src.frames-pos:block;src.offset=pos;
            AudioTimeStamp ts={0};ts.mSampleTime=pos;ts.mFlags=kAudioTimeStampSampleTimeValid;
            AudioUnitRenderActionFlags flags=0;
            require(AudioUnitRender(unit,&flags,&ts,0,count,(AudioBufferList *)&buffers),"render");
            for (UInt32 i=0;i<count;i++) {frame[0]=((float *)buffers.buffers[0].mData)[i];frame[1]=((float *)buffers.buffers[1].mData)[i];if(fwrite(frame,4,2,out)!=2)return 2;}
        }
        if (fclose(out))return 2;
        free(buffers.buffers[0].mData);free(buffers.buffers[1].mData);free(src.input);
        require(AudioUnitUninitialize(unit),"uninitialize");
    } else if (strcmp(argv[4],"info")) return 2;
    for (uint32_t i=0;i<_dyld_image_count();i++) printf("IMAGE\t%s\n",_dyld_get_image_name(i));
    require(AudioComponentInstanceDispose(unit),"dispose");
    return 0;
}
