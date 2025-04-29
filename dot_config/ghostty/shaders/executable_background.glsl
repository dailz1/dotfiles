#version 330 core

out vec4 FragColor;

in vec2 TexCoord;

uniform sampler2D backgroundTexture; // 自定义图片
uniform sampler2D terminalTexture;  // 终端内容
uniform float terminalAlpha;        // 终端透明度

void main() {
    // 加载自定义图片
    vec4 background = texture(backgroundTexture, TexCoord);

    // 加载终端内容
    vec4 terminal = texture(terminalTexture, TexCoord);

    // 混合背景和终端内容
    float alpha = terminal.a * terminalAlpha; // 使用终端内容的透明度，并乘以自定义透明度
    FragColor = mix(background, terminal, alpha);
}
