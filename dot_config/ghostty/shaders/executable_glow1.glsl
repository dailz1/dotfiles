void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord/iResolution.xy;
    
    // Base color from terminal
    vec3 color = texture(iChannel0, uv).rgb;
    
    // 简单的静态效果
    float brightness = 0.9;    // 提高亮度到 0.9
    float contrast = 0.9;      // 保持相同的对比度
    
    // 应用柔和的颜色调整
    color = color * brightness;
    color = mix(vec3(0.5), color, contrast);
    
    fragColor = vec4(color, 1.0);
}