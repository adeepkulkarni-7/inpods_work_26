// Task Manager - Shared across all standalone apps
// Handles async task tracking and notifications

const TaskState = {
    PENDING: 'pending',
    RUNNING: 'running',
    COMPLETED: 'completed',
    FAILED: 'failed'
};

class TaskManager {
    constructor() {
        this.tasks = new Map();
        this.counter = 0;
    }

    create(type, description) {
        const id = `task_${++this.counter}_${Date.now()}`;
        const task = {
            id,
            type,
            description,
            state: TaskState.PENDING,
            progress: 0,
            startTime: null,
            endTime: null,
            result: null,
            error: null
        };
        this.tasks.set(id, task);
        this.render();
        return id;
    }

    async run(taskId, asyncFn) {
        const task = this.tasks.get(taskId);
        if (!task) return null;

        task.state = TaskState.RUNNING;
        task.startTime = Date.now();
        this.render();

        try {
            task.result = await asyncFn((p) => {
                task.progress = p;
                this.render();
            });
            task.state = TaskState.COMPLETED;
        } catch (e) {
            task.state = TaskState.FAILED;
            task.error = e.message;
        }

        task.endTime = Date.now();
        this.render();
        this.notifyComplete(task);
        return task;
    }

    notifyComplete(task) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const icon = task.state === TaskState.COMPLETED ? '\u2713' : '\u2717';
            new Notification(`${icon} ${this.getTypeLabel(task.type)}`, {
                body: task.description
            });
        }
        // Also show status bar notification
        const type = task.state === TaskState.COMPLETED ? 'success' : 'error';
        showStatus(`${this.getTypeLabel(task.type)}: ${task.state === TaskState.COMPLETED ? 'Complete' : task.error}`, type);
    }

    getTypeLabel(type) {
        const labels = {
            'mapping': 'Question Mapping',
            'rating': 'Mapping Validation',
            'insights': 'Insights Generation'
        };
        return labels[type] || type;
    }

    getActive() {
        return [...this.tasks.values()].filter(t => t.state === TaskState.RUNNING);
    }

    getAll() {
        return [...this.tasks.values()].sort((a, b) => (b.startTime || 0) - (a.startTime || 0));
    }

    render() {
        const tasks = this.getAll();
        const active = this.getActive();
        const panel = document.getElementById('taskPanel');
        const list = document.getElementById('taskList');
        const count = document.getElementById('activeTaskCount');

        if (!panel || !list || !count) return;

        count.textContent = active.length;
        count.classList.toggle('zero', active.length === 0);
        panel.classList.toggle('has-active', active.length > 0);

        if (tasks.length === 0) {
            list.innerHTML = '<div class="task-empty">No tasks yet</div>';
            return;
        }

        list.innerHTML = tasks.slice(0, 10).map(t => {
            const dur = t.endTime
                ? this.formatDur(t.endTime - t.startTime)
                : t.startTime
                    ? this.formatDur(Date.now() - t.startTime) + '...'
                    : '';
            return `
                <div class="task-item ${t.state}">
                    <div class="task-item-header">
                        <span class="task-item-type">${this.getTypeLabel(t.type)}</span>
                        <span class="task-item-status ${t.state}">${t.state}</span>
                    </div>
                    <div class="task-item-desc">${t.description}</div>
                    ${t.state === 'running' ? `<div class="task-progress"><div class="task-progress-fill" style="width:${t.progress}%"></div></div>` : ''}
                    ${dur ? `<div class="task-item-time">${dur}</div>` : ''}
                    ${t.error ? `<div class="task-item-desc" style="color:#ef4444">${t.error}</div>` : ''}
                </div>
            `;
        }).join('');
    }

    formatDur(ms) {
        const s = Math.floor(ms / 1000);
        return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
    }
}

// Global task manager instance
const taskManager = new TaskManager();

function toggleTaskPanel() {
    const panel = document.getElementById('taskPanel');
    const icon = document.getElementById('taskPanelToggleIcon');
    if (panel && icon) {
        panel.classList.toggle('collapsed');
        icon.textContent = panel.classList.contains('collapsed') ? '\u25B2' : '\u25BC';
    }
}

// Request notification permission on load
if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}
