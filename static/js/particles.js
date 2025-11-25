/**
 * 悬浮粒子动画系统
 * 轻量级、柔和、透明的粒子效果
 */
class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.particleCount = 50; // 粒子数量
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        this.resize();
        this.createParticles();
        this.animate();
        
        // 窗口大小改变时重新调整
        window.addEventListener('resize', () => {
            this.resize();
            this.createParticles();
        });
    }
    
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    createParticles() {
        this.particles = [];
        for (let i = 0; i < this.particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                radius: Math.random() * 2 + 1, // 1-3px
                vx: (Math.random() - 0.5) * 0.5, // 速度 x
                vy: (Math.random() - 0.5) * 0.5, // 速度 y
                opacity: Math.random() * 0.5 + 0.2, // 0.2-0.7 透明度
                color: this.getRandomColor()
            });
        }
    }
    
    getRandomColor() {
        // 柔和的渐变色系
        const colors = [
            'rgba(0, 122, 255, ', // 蓝色
            'rgba(88, 86, 214, ', // 紫色
            'rgba(255, 149, 0, ', // 橙色
            'rgba(52, 199, 89, ', // 绿色
            'rgba(90, 200, 250, ' // 浅蓝色
        ];
        return colors[Math.floor(Math.random() * colors.length)];
    }
    
    updateParticle(particle) {
        // 更新位置
        particle.x += particle.vx;
        particle.y += particle.vy;
        
        // 边界检测和反弹
        if (particle.x < 0 || particle.x > this.canvas.width) {
            particle.vx = -particle.vx;
        }
        if (particle.y < 0 || particle.y > this.canvas.height) {
            particle.vy = -particle.vy;
        }
        
        // 确保粒子在画布内
        particle.x = Math.max(0, Math.min(this.canvas.width, particle.x));
        particle.y = Math.max(0, Math.min(this.canvas.height, particle.y));
        
        // 轻微的随机运动变化
        particle.vx += (Math.random() - 0.5) * 0.02;
        particle.vy += (Math.random() - 0.5) * 0.02;
        
        // 限制速度
        particle.vx = Math.max(-1, Math.min(1, particle.vx));
        particle.vy = Math.max(-1, Math.min(1, particle.vy));
    }
    
    drawParticle(particle) {
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = particle.color + particle.opacity + ')';
        this.ctx.fill();
    }
    
    drawConnections() {
        // 绘制粒子之间的连线
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                // 只连接距离较近的粒子
                if (distance < 150) {
                    const opacity = (1 - distance / 150) * 0.1; // 距离越远越透明
                    this.ctx.beginPath();
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.strokeStyle = `rgba(0, 122, 255, ${opacity})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.stroke();
                }
            }
        }
    }
    
    animate() {
        // 清空画布（使用半透明以创建拖尾效果）
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // 更新和绘制所有粒子
        this.particles.forEach(particle => {
            this.updateParticle(particle);
            this.drawParticle(particle);
        });
        
        // 绘制连线
        this.drawConnections();
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }
}

// 初始化粒子系统
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('particle-canvas');
    if (canvas) {
        window.particleSystem = new ParticleSystem(canvas);
    }
});

