// Modern Calendar - Pure JavaScript (No external dependencies except Font Awesome)

class ModernCalendar {
    constructor(element, options = {}) {
        this.element = element;
        this.currentDate = options.currentDate || new Date();
        this.onDateClick = options.onDateClick || null;
        this.onTaskClick = options.onTaskClick || null;
        this.tasks = options.tasks || [];
        this.render();
    }
    
    getDaysInMonth(year, month) {
        return new Date(year, month + 1, 0).getDate();
    }
    
    getFirstDayOfMonth(year, month) {
        return new Date(year, month, 1).getDay();
    }
    
    formatDate(year, month, day) {
        return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    }
    
    getTasksForDate(date) {
        return this.tasks.filter(task => task.deadline && task.deadline.split('T')[0] === date);
    }
    
    getStatusColor(status) {
        const colors = {
            'TODO': '#ef4444',
            'IN_PROGRESS': '#f59e0b',
            'DONE': '#10b981'
        };
        return colors[status] || '#6366f1';
    }
    
    previousMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        this.render();
    }
    
    nextMonth() {
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        this.render();
    }
    
    goToToday() {
        this.currentDate = new Date();
        this.render();
    }
    
    render() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const today = new Date();
        
        const daysInMonth = this.getDaysInMonth(year, month);
        const firstDay = this.getFirstDayOfMonth(year, month);
        
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December'];
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        let html = `
            <div class="calendar-container">
                <div class="calendar-header">
                    <button class="calendar-nav-btn" onclick="window.calendar.previousMonth()">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <h2 class="calendar-title">${monthNames[month]} ${year}</h2>
                    <button class="calendar-nav-btn" onclick="window.calendar.nextMonth()">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                    <button class="calendar-today-btn" onclick="window.calendar.goToToday()">
                        <i class="fas fa-calendar-day"></i> Today
                    </button>
                </div>
                
                <div class="calendar-weekdays">
                    ${dayNames.map(day => `<div class="calendar-weekday">${day}</div>`).join('')}
                </div>
                
                <div class="calendar-days">
        `;
        
        // Empty cells for days before month starts
        for (let i = 0; i < firstDay; i++) {
            html += `<div class="calendar-day empty"></div>`;
        }
        
        // Days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = this.formatDate(year, month, day);
            const dayTasks = this.getTasksForDate(dateStr);
            const isToday = today.getFullYear() === year && today.getMonth() === month && today.getDate() === day;
            const hasTasks = dayTasks.length > 0;
            
            let tasksHtml = '';
            if (hasTasks) {
                const displayTasks = dayTasks.slice(0, 3);
                tasksHtml = `
                    <div class="calendar-day-tasks">
                        ${displayTasks.map(task => `
                            <div class="calendar-task-badge" style="background: ${this.getStatusColor(task.status)}" 
                                 onclick="event.stopPropagation(); window.calendar.onTaskClick && window.calendar.onTaskClick(task)">
                                ${task.title.length > 20 ? task.title.substring(0, 20) + '...' : task.title}
                            </div>
                        `).join('')}
                        ${dayTasks.length > 3 ? `<div class="calendar-task-more">+${dayTasks.length - 3} more</div>` : ''}
                    </div>
                `;
            }
            
            html += `
                <div class="calendar-day ${isToday ? 'today' : ''} ${hasTasks ? 'has-tasks' : ''}" 
                     data-date="${dateStr}" onclick="window.calendar.onDateClick && window.calendar.onDateClick('${dateStr}')">
                    <div class="calendar-day-number">${day}</div>
                    ${tasksHtml}
                </div>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
        
        this.element.innerHTML = html;
    }
    
    updateTasks(tasks) {
        this.tasks = tasks;
        this.render();
    }
}

// Make calendar globally available
window.ModernCalendar = ModernCalendar;