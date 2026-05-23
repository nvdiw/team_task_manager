// Simple Chart Library - No dependencies
const SimpleChart = {
    // Draw a pie chart
    pie: function(canvasId, data, colors) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 10;
        
        let startAngle = -Math.PI / 2;
        const total = data.reduce((a, b) => a + b, 0);
        
        ctx.clearRect(0, 0, width, height);
        
        for (let i = 0; i < data.length; i++) {
            const angle = (data[i] / total) * Math.PI * 2;
            const endAngle = startAngle + angle;
            
            ctx.beginPath();
            ctx.fillStyle = colors[i];
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.closePath();
            ctx.fill();
            
            startAngle = endAngle;
        }
        
        // Draw border
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
    },
    
    // Draw a bar chart
    bar: function(canvasId, labels, data, colors) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        const barWidth = (width - 100) / labels.length - 10;
        const maxData = Math.max(...data, 1);
        const scaleY = (height - 80) / maxData;
        
        ctx.clearRect(0, 0, width, height);
        
        // Draw axes
        ctx.beginPath();
        ctx.strokeStyle = '#666';
        ctx.lineWidth = 1;
        ctx.moveTo(40, 20);
        ctx.lineTo(40, height - 40);
        ctx.lineTo(width - 20, height - 40);
        ctx.stroke();
        
        // Draw bars
        for (let i = 0; i < data.length; i++) {
            const x = 50 + i * (barWidth + 10);
            const barHeight = data[i] * scaleY;
            const y = height - 40 - barHeight;
            
            ctx.fillStyle = colors[i % colors.length];
            ctx.fillRect(x, y, barWidth, barHeight);
            
            // Draw label
            ctx.fillStyle = '#333';
            ctx.font = '12px Arial';
            ctx.fillText(labels[i], x, height - 25);
            
            // Draw value on top of bar
            ctx.fillStyle = '#333';
            ctx.fillText(data[i], x + barWidth / 4, y - 5);
        }
    },

    // Draw a doughnut chart (for progress)
    doughnut: function(canvasId, data, colors) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 5;
        let startAngle = -Math.PI / 2;
        const total = data.reduce((a, b) => a + b, 0);
        
        ctx.clearRect(0, 0, width, height);
        
        for (let i = 0; i < data.length; i++) {
            const angle = (data[i] / total) * Math.PI * 2;
            const endAngle = startAngle + angle;
            ctx.beginPath();
            ctx.fillStyle = colors[i];
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.closePath();
            ctx.fill();
            startAngle = endAngle;
        }
        
        // Draw inner circle to make it a doughnut
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius * 0.65, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.fill();
    }
};