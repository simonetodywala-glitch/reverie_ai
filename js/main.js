// Generate twinkling star field background
const container = document.getElementById('stars');

for (let i = 0; i < 140; i++) {
  const star = document.createElement('div');
  star.className = 'star';

  const size = Math.random() * 2.5 + 0.5;

  star.style.cssText = `
    width: ${size}px;
    height: ${size}px;
    left: ${Math.random() * 100}%;
    top: ${Math.random() * 100}%;
    --dur: ${2 + Math.random() * 4}s;
    --min-op: ${0.05 + Math.random() * 0.15};
    --max-op: ${0.3 + Math.random() * 0.55};
    animation-delay: ${Math.random() * 5}s;
  `;

  container.appendChild(star);
}
