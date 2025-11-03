// Matrix rain effect
const canvas = document.getElementById('matrix-bg');
const ctx = canvas.getContext('2d');

// Set canvas size
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

// Characters to use - mix of numbers, letters, and symbols
const chars = '01$¥€£ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%^&*()';
const charArray = chars.split('');

const fontSize = 14;
const columns = canvas.width / fontSize;

// Array to store y position and color for each column
const drops = [];
const colors = [
    '#00ff41',  // Matrix green
    '#00d9ff',  // Cyan
    '#ff0055',  // Pink/Red
    '#ffa500',  // Orange
    '#9d00ff',  // Purple
    '#00ffff',  // Bright cyan
    '#ff00ff',  // Magenta
];

for (let i = 0; i < columns; i++) {
    drops[i] = {
        y: Math.random() * -100,
        color: colors[Math.floor(Math.random() * colors.length)],
        speed: 0.3 + Math.random() * 0.3  // Random speed between 0.3-0.6
    };
}

// Draw function
function draw() {
    // Black background with slight transparency for trail effect
    ctx.fillStyle = 'rgba(0, 0, 0, 0.08)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.font = fontSize + 'px monospace';
    
    // Loop through drops
    for (let i = 0; i < drops.length; i++) {
        const drop = drops[i];
        
        // Random character
        const text = charArray[Math.floor(Math.random() * charArray.length)];
        
        // Set color for this drop
        ctx.fillStyle = drop.color;
        
        // Add glow effect
        ctx.shadowBlur = 10;
        ctx.shadowColor = drop.color;
        
        // Draw character
        ctx.fillText(text, i * fontSize, drop.y * fontSize);
        
        // Reset shadow
        ctx.shadowBlur = 0;
        
        // Reset drop to top randomly after it crosses screen
        if (drop.y * fontSize > canvas.height && Math.random() > 0.975) {
            drop.y = 0;
            drop.color = colors[Math.floor(Math.random() * colors.length)];
            drop.speed = 0.3 + Math.random() * 0.3;
        }
        
        // Increment Y position with individual speed
        drop.y += drop.speed;
    }
}

// Animation loop - slower refresh rate
setInterval(draw, 50); // ~20 FPS (slower)

// Resize canvas on window resize
window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});
