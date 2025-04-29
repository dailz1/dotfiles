// ShaderToy兼容性修改
#ifndef SHADERTOY
uniform sampler2D tex;
uniform sampler2D myChannel0;  // 重命名避免冲突
uniform vec2 myResolution;     // 重命名避免冲突
uniform float blurRadius;      // 可通过配置文件动态调整
#define iChannel0 myChannel0
#define iResolution myResolution
#endif

// 保留原始颜色空间转换函数
float f(float x){
    return(x>=.0031308)?1.055*pow(x,1./2.4)-.055:12.92*x;
}

float f_inv(float x){
    return(x>=.04045)?pow((x+.055)/1.055,2.4):x/12.92;
}

vec4 toOklab(vec4 rgb){
    vec3 c=vec3(f_inv(rgb.r),f_inv(rgb.g),f_inv(rgb.b));
    float l=.4122214708*c.r+.5363325363*c.g+.0514459929*c.b;
    float m=.2119034982*c.r+.6806995451*c.g+.1073969566*c.b;
    float s=.0883024619*c.r+.2817188376*c.g+.6299787005*c.b;
    return vec4(
        .2104542553*pow(l,1./3.)+.7936177850*pow(m,1./3.)-.0040720468*pow(s,1./3.),
        1.9779984951*pow(l,1./3.)-2.4285922050*pow(m,1./3.)+.4505937099*pow(s,1./3.),
        .0259040371*pow(l,1./3.)+.7827717662*pow(m,1./3.)-.8086757660*pow(s,1./3.),
        rgb.a
    );
}

vec4 toRgb(vec4 oklab){
    float l_=oklab.x+.3963377774*oklab.y+.2158037573*oklab.z;
    float m_=oklab.x-.1055613458*oklab.y-.0638541728*oklab.z;
    float s_=oklab.x-.0894841775*oklab.y-1.2914855480*oklab.z;
    float l_pow = pow(l_, 3.0);
    float m_pow = pow(m_, 3.0);
    float s_pow = pow(s_, 3.0);
    vec3 linear=vec3(
        4.0767416621*l_pow-3.3077115913*m_pow+.2309699292*s_pow,
        -1.2684380046*l_pow+2.6097574011*m_pow-.3413193965*s_pow,
        -.0041960863*l_pow-.7034186147*m_pow+1.7076147010*s_pow
    );
    return vec4(f(linear.r),f(linear.g),f(linear.b),oklab.a);
}

vec4 edgeAwareBlur(vec2 uv,vec2 step){
    // 初始边缘检测
    vec4 center=texture(iChannel0,uv);
    float edge=0.;
    
    // Sobel 算子边缘检测
    vec4 samples[9];
    for(int x=-1;x<=1;++x){
        for(int y=-1;y<=1;++y){
            samples[(x+1)*3+(y+1)]=texture(iChannel0,uv+vec2(x,y)*step);
        }
    }
    
    float gx=(samples[2].a-samples[0].a)*2.
    +(samples[5].a-samples[3].a)
    +(samples[8].a-samples[6].a);
    
    float gy=(samples[6].a-samples[0].a)*2.
    +(samples[7].a-samples[1].a)
    +(samples[8].a-samples[2].a);
    
    edge=clamp(length(vec2(gx,gy))*10.,0.,1.);
    
    // 动态模糊半径
    float actualRadius=blurRadius*(1.-edge*.8);
    float sigma=actualRadius/2.;
    
    // 水平模糊
    vec4 horizBlur=vec4(0.);
    float total=0.;
    for(float x=-actualRadius;x<=actualRadius;x+=1.){
        float weight=exp(-x*x/(2.*sigma*sigma));
        horizBlur+=texture(iChannel0,uv+vec2(x,0.)*step)*weight;
        total+=weight;
    }
    horizBlur/=total;
    
    // 垂直模糊
    vec4 finalBlur=vec4(0.);
    total=0.;
    for(float y=-actualRadius;y<=actualRadius;y+=1.){
        float weight=exp(-y*y/(2.*sigma*sigma));
        finalBlur+=texture(iChannel0,uv+vec2(0.,y)*step)*weight;
        total+=weight;
    }
    finalBlur/=total;
    
    // 混合原始颜色和模糊结果
    return mix(finalBlur,center,edge*.7);
}

void mainImage(out vec4 fragColor,in vec2 fragCoord){
    vec2 uv=fragCoord.xy/iResolution.xy;
    vec2 step=1./iResolution.xy;
    
    // 执行边缘感知模糊
    vec4 blurred=edgeAwareBlur(uv,step);
    
    // 颜色空间转换处理
    vec4 oklabBlur=toOklab(blurred);
    vec4 finalColor=toRgb(oklabBlur);
    
    // 透明度控制 (0.5-0.8 根据边缘强度变化)
    finalColor.a=mix(.8,.5,length(texture(iChannel0,uv).a-blurred.a));
    
    fragColor=finalColor;
}

// ShaderToy入口点
void main(){
    mainImage(gl_FragColor,gl_FragCoord.xy);
}


