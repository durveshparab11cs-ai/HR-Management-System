/**
 * motion.js
 * High-performance motion and UI micro-interactions
 * CS Creative Solutions - Smart HRMS
 */

(function () {
  'use strict';

  // ── 1. Animated Count-Up Numbers (Real Values Only) ──
  window.animateNumber = function (element, targetValue, duration = 800) {
    if (!element) return;
    const startValue = 0;
    const startTime = performance.now();
    const isDecimal = targetValue.toString().includes('.');

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Easing: easeOutExpo
      const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
      const current = startValue + (targetValue - startValue) * ease;

      element.textContent = isDecimal
        ? current.toFixed(2)
        : Math.round(current).toLocaleString('en-IN');

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = isDecimal
          ? targetValue.toFixed(2)
          : Number(targetValue).toLocaleString('en-IN');
      }
    }

    requestAnimationFrame(update);
  };

  // ── 2. Gliding Tab Component ──
  window.initGlidingTabs = function (containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const tabs = container.querySelectorAll('.tab-btn');
    const glider = container.querySelector('.tab-glider');

    function updateGlider(activeTab) {
      if (!glider || !activeTab) return;
      glider.style.width = `${activeTab.offsetWidth}px`;
      glider.style.left = `${activeTab.offsetLeft}px`;
    }

    tabs.forEach((tab) => {
      tab.addEventListener('click', function () {
        tabs.forEach((t) => t.classList.remove('active'));
        this.classList.add('active');
        updateGlider(this);
      });
    });

    const currentActive = container.querySelector('.tab-btn.active') || tabs[0];
    if (currentActive) {
      updateGlider(currentActive);
    }
  };

  // ── 3. Interactive Background Canvas (3D Constellation / Mesh) ──
  window.initHeroCanvas = function (canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    let particles = [];
    const count = Math.floor(Math.min(width, height) / 22);

    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        size: Math.random() * 2 + 1,
        alpha: Math.random() * 0.5 + 0.2,
      });
    }

    let mouse = { x: -1000, y: -1000 };
    window.addEventListener('mousemove', (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    });

    function draw() {
      ctx.clearRect(0, 0, width, height);

      // Deep radial glow
      const grad = ctx.createRadialGradient(
        width / 2,
        height * 0.4,
        50,
        width / 2,
        height * 0.4,
        width * 0.8
      );
      grad.addColorStop(0, 'rgba(16, 31, 74, 0.4)');
      grad.addColorStop(1, 'rgba(4, 8, 20, 0.95)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      // Connect lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 130) {
            ctx.strokeStyle = `rgba(59, 130, 246, ${0.15 * (1 - dist / 130)})`;
            ctx.lineWidth = 0.8;
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw points
      for (let p of particles) {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        // Interaction with mouse
        const mdx = mouse.x - p.x;
        const mdy = mouse.y - p.y;
        const mdist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mdist < 100) {
          p.x -= (mdx / mdist) * 1.5;
          p.y -= (mdy / mdist) * 1.5;
        }

        ctx.fillStyle = `rgba(96, 165, 250, ${p.alpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      }

      requestAnimationFrame(draw);
    }

    draw();

    window.addEventListener('resize', () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    });
  };

  // ── 4. Trigger Error Shake Animation ──
  window.triggerErrorShake = function (elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.classList.remove('motion-shake');
    void el.offsetWidth; // Force reflow
    el.classList.add('motion-shake');
  };
})();
