/**
 * 动态波浪流动动画系统
 * 轻盈、现代的液体波浪效果
 */
class WaveAnimation {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.waves = [];
        this.animationId = null;
        this.time = 0;
        
        this.init();
    }
    
    init() {
        this.resize();
        this.createWaves();
        this.animate();
        
        // 窗口大小改变时重新调整
        window.addEventListener('resize', () => {
            this.resize();
            this.createWaves();
        });
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createWaves() {
        // 创建多层波浪，营造深度感
        this.waves = [
            {
                amplitude: 60,      // 波浪幅度
                frequency: 0.0008,   // 频率（控制波浪密度）
                speed: 0.0003,      // 移动速度
                phase: 0,           // 相位
                color: 'rgba(0, 122, 255, 0.15)', // 蓝色，低透明度
                yOffset: this.canvas.height * 0.7  // Y轴偏移
            },
            {
                amplitude: 80,
                frequency: 0.0006,
                speed: 0.0004,
                phase: Math.PI / 3,
                color: 'rgba(88, 86, 214, 0.12)', // 紫色，低透明度
                yOffset: this.canvas.height * 0.75
            },
            {
                amplitude: 50,
                frequency: 0.001,
                speed: 0.00025,
                phase: Math.PI / 2,
                color: 'rgba(90, 200, 250, 0.1)', // 青色，低透明度
                yOffset: this.canvas.height * 0.8
            },
            {
                amplitude: 70,
                frequency: 0.0007,
                speed: 0.00035,
                phase: Math.PI,
                color: 'rgba(0, 150, 255, 0.08)', // 深蓝色，低透明度
                yOffset: this.canvas.height * 0.85
            }
        ];
    }
    
    drawWave(wave) {
        this.ctx.beginPath();
        this.ctx.moveTo(0, this.canvas.height);
        
        // 绘制波浪路径
        for (let x = 0; x <= this.canvas.width; x += 1) {
            const y = wave.yOffset + 
                     Math.sin(x * wave.frequency + this.time * wave.speed + wave.phase) * wave.amplitude;
            this.ctx.lineTo(x, y);
        }
        
        // 闭合路径到底部
        this.ctx.lineTo(this.canvas.width, this.canvas.height);
        this.ctx.lineTo(0, this.canvas.height);
        this.ctx.closePath();
        
        // 填充波浪
        this.ctx.fillStyle = wave.color;
        this.ctx.fill();
    }
    
    animate() {
        // 清空画布
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 更新时间
        this.time += 1;
        
        // 绘制所有波浪层
        this.waves.forEach(wave => {
            this.drawWave(wave);
        });
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

// 初始化波浪动画
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('wave-canvas');
    if (canvas) {
        window.waveAnimation = new WaveAnimation(canvas);
    }
});

