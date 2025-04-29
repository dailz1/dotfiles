// sRGB linear -> nonlinear transform from https://bottosson.github.io/posts/colorwrong/
float f(float x) {
    if (x >= 0.0031308) {
        return 1.055 * pow(x, 1.0 / 2.4) - 0.055;
    } else {
        return 12.92 * x;
    }
}

float f_inv(float x) {
    if (x >= 0.04045) {
        return pow((x + 0.055) / 1.055, 2.4);
    } else {
        return x / 12.92;
    }
}

// Oklab <-> linear sRGB conversions from https://bottosson.github.io/posts/oklab/
vec4 toOklab(vec4 rgb) {
    vec3 c = vec3(f_inv(rgb.r), f_inv(rgb.g), f_inv(rgb.b));
    float l = 0.4122214708 * c.r + 0.5363325363 * c.g + 0.0514459929 * c.b;
    float m = 0.2119034982 * c.r + 0.6806995451 * c.g + 0.1073969566 * c.b;
    float s = 0.0883024619 * c.r + 0.2817188376 * c.g + 0.6299787005 * c.b;
    float l_ = pow(l, 1.0 / 3.0);
    float m_ = pow(m, 1.0 / 3.0);
    float s_ = pow(s, 1.0 / 3.0);
    return vec4(
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
        rgb.a
    );
}

vec4 toRgb(vec4 oklab) {
    vec3 c = oklab.rgb;
    float l_ = c.r + 0.3963377774 * c.g + 0.2158037573 * c.b;
    float m_ = c.r - 0.1055613458 * c.g - 0.0638541728 * c.b;
    float s_ = c.r - 0.0894841775 * c.g - 1.2914855480 * c.b;
    float l = l_ * l_ * l_;
    float m = m_ * m_ * m_;
    float s = s_ * s_ * s_;
    vec3 linear_srgb = vec3(
         4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    );
    return vec4(
        clamp(f(linear_srgb.r), 0.0, 1.0),
        clamp(f(linear_srgb.g), 0.0, 1.0),
        clamp(f(linear_srgb.b), 0.0, 1.0),
        oklab.a
    );
}

// Bloom samples from https://gist.github.com/qwerasd205/c3da6c610c8ffe17d6d2d3cc7068f17f
const vec3[24] samples = {
  vec3(0.1693761725038636, 0.9855514761735895, 1),
  vec3(-1.333070830962943, 0.4721463328627773, 0.7071067811865475),
  vec3(-0.8464394909806497, -1.51113870578065, 0.5773502691896258),
  vec3(1.554155680728463, -1.2588090085709776, 0.5),
  vec3(1.681364377589461, 1.4741145918052656, 0.4472135954999579),
  vec3(-1.2795157692199817, 2.088741103228784, 0.4082482904638631),
  vec3(-2.4575847530631187, -0.9799373355024756, 0.3779644730092272),
  vec3(0.5874641440200847, -2.7667464429345077, 0.35355339059327373),
  vec3(2.997715703369726, 0.11704939884745152, 0.3333333333333333),
  vec3(0.41360842451688395, 3.1351121305574803, 0.31622776601683794),
  vec3(-3.167149933769243, 0.9844599011770256, 0.30151134457776363),
  vec3(-1.5736713846521535, -3.0860263079123245, 0.2886751345948129),
  vec3(2.888202648340422, -2.1583061557896213, 0.2773500981126146),
  vec3(2.7150778983300325, 2.5745586041105715, 0.2672612419124244),
  vec3(-2.1504069972377464, 3.2211410627650165, 0.2581988897471611),
  vec3(-3.6548858794907493, -1.6253643308191343, 0.25),
  vec3(1.0130775986052671, -3.9967078676335834, 0.24253562503633297),
  vec3(4.229723673607257, 0.33081361055181563, 0.23570226039551587),
  vec3(0.40107790291173834, 4.340407413572593, 0.22941573387056174),
  vec3(-4.319124570236028, 1.159811599693438, 0.22360679774997896),
  vec3(-1.9209044802827355, -4.160543952132907, 0.2182178902359924),
  vec3(3.8639122286635708, -2.6589814382925123, 0.21320071635561041),
  vec3(3.3486228404946234, 3.4331800232609, 0.20851441405707477),
  vec3(-2.8769733643574344, 3.9652268864187157, 0.20412414523193154)
};

// 降低亮度阈值，减少发光区域
const float DIM_CUTOFF = 0.55;  // 提高暗部阈值
const float BRIGHT_CUTOFF = 0.85;  // 提高亮部阈值

// 高斯权重数组（sigma = 3.0）
const float gaussian_weights[5] = float[](
    0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216
);

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec4 source = toOklab(texture(iChannel0, uv));
    vec4 dest = source;

    if (source.x > DIM_CUTOFF) {
        dest.x *= 1.01;  // 降低亮部增强
    } else {
        vec2 texelSize = 1.0 / iResolution.xy;
        vec3 glow = vec3(0.0);
        
        // 中心像素
        vec3 blur = source.xyz * gaussian_weights[0];
        float totalWeight = gaussian_weights[0];
        
        // 两次循环分别处理水平和垂直方向
        for (int i = 1; i < 5; i++) {
            float weight = gaussian_weights[i];
            vec2 offset = texelSize * float(i);
            
            // 水平方向
            vec4 h1 = toOklab(texture(iChannel0, uv + vec2(offset.x, 0.0)));
            vec4 h2 = toOklab(texture(iChannel0, uv - vec2(offset.x, 0.0)));
            
            // 垂直方向
            vec4 v1 = toOklab(texture(iChannel0, uv + vec2(0.0, offset.y)));
            vec4 v2 = toOklab(texture(iChannel0, uv - vec2(0.0, offset.y)));

            // 对亮度超过阈值的像素进行模糊处理
            if (h1.x > DIM_CUTOFF) {
                blur += h1.xyz * weight;
                totalWeight += weight;
            }
            if (h2.x > DIM_CUTOFF) {
                blur += h2.xyz * weight;
                totalWeight += weight;
            }
            if (v1.x > DIM_CUTOFF) {
                blur += v1.xyz * weight;
                totalWeight += weight;
            }
            if (v2.x > DIM_CUTOFF) {
                blur += v2.xyz * weight;
                totalWeight += weight;
            }
        }
        
        // 归一化模糊结果
        blur /= totalWeight;
        
        // 根据亮度值调整发光强度
        if (blur.x <= BRIGHT_CUTOFF) {
            glow = blur * 0.025;  // 降低暗部发光
        } else {
            glow = blur * 0.035;  // 降低亮部发光
        }
        
        float edgeFactor = 1.0 - length(uv - 0.5) * 1.2;
        // 移除闪烁效果
        // float edgePulse = sin(iTime * 2.0 + length(uv - 0.5) * 5.0);
        edgeFactor = clamp(edgeFactor, 0.0, 1.0);
        glow *= edgeFactor;
        
        dest.xyz += glow;
    }

    fragColor = toRgb(dest);
}