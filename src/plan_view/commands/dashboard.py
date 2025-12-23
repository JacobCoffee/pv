"""Dashboard command for viewing and editing plan in browser."""

import argparse
import http.server
import json
import os
import socket
import socketserver
import webbrowser
from pathlib import Path

from plan_view.decorators import require_plan
from plan_view.formatting import now_iso
from plan_view.io import load_plan, save_plan
from plan_view.state import find_phase, find_task

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Plan Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
  <link href="https://cdn.jsdelivr.net/npm/daisyui@5/themes.css" rel="stylesheet" type="text/css" />
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
  <style>
    .phase-card { transition: all 0.2s ease; }
    .phase-card:hover { transform: translateY(-2px); }
    .task-item { transition: background-color 0.15s ease; }
    .status-badge { font-size: 0.7rem; }
    .copy-btn { opacity: 0.6; transition: opacity 0.15s; }
    .copy-btn:hover { opacity: 1; }
    .action-btn { opacity: 0.7; transition: opacity 0.15s; }
    .action-btn:hover { opacity: 1; }
    .prompt-text { font-family: ui-monospace, monospace; font-size: 0.85rem; }
  </style>
</head>
<body class="min-h-screen bg-base-200">
  <div class="navbar bg-base-100 shadow-lg sticky top-0 z-50">
    <div class="flex-1"><span class="text-xl font-bold px-4">Plan Dashboard</span></div>
    <div class="flex-none gap-2">
      <button class="btn btn-ghost btn-sm" onclick="loadAndRender()" title="Refresh">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
      <div class="dropdown dropdown-end">
        <div tabindex="0" role="button" class="btn btn-ghost btn-circle">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
          </svg>
        </div>
        <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow">
          <li><a onclick="setTheme('light')">Light</a></li>
          <li><a onclick="setTheme('dark')">Dark</a></li>
          <li><a onclick="setTheme('synthwave')">Synthwave</a></li>
          <li><a onclick="setTheme('cyberpunk')">Cyberpunk</a></li>
          <li><a onclick="setTheme('forest')">Forest</a></li>
        </ul>
      </div>
    </div>
  </div>
  <div class="container mx-auto px-4 py-8 max-w-7xl">
    <div id="loading" class="flex justify-center items-center h-64">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>
    <div id="error" class="hidden">
      <div class="alert alert-error">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
        <span id="error-message">Failed to load plan.json</span>
      </div>
    </div>
    <div id="content" class="hidden">
      <div id="header" class="mb-8"></div>
      <div id="summary" class="mb-8"></div>
      <div id="phases" class="space-y-6"></div>
      <div id="decisions" class="mt-8"></div>
      <div id="blockers" class="mt-8"></div>
      <div id="ai-prompts" class="mt-8"></div>
    </div>
  </div>
  <div class="toast toast-end" id="toast-container"></div>

  <!-- Task Actions Modal -->
  <dialog id="task-modal" class="modal">
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4" id="task-modal-title">Task Actions</h3>
      <div id="task-modal-content"></div>
      <div class="modal-action">
        <form method="dialog"><button class="btn">Close</button></form>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop"><button>close</button></form>
  </dialog>

  <!-- Add Task Modal -->
  <dialog id="add-task-modal" class="modal">
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4">Add New Task</h3>
      <div class="form-control gap-4">
        <input type="hidden" id="add-task-phase" />
        <div>
          <label class="label"><span class="label-text">Title</span></label>
          <input type="text" id="add-task-title" class="input input-bordered w-full" placeholder="Task title" />
        </div>
        <div>
          <label class="label"><span class="label-text">Agent Type (optional)</span></label>
          <input type="text" id="add-task-agent" class="input input-bordered w-full" placeholder="e.g., python-backend-engineer" />
        </div>
        <div>
          <label class="label"><span class="label-text">Skill (optional)</span></label>
          <input type="text" id="add-task-skill" class="input input-bordered w-full" placeholder="e.g., test, review, build" />
        </div>
      </div>
      <div class="modal-action">
        <button class="btn btn-primary" onclick="submitAddTask()">Add Task</button>
        <form method="dialog"><button class="btn">Cancel</button></form>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop"><button>close</button></form>
  </dialog>

  <!-- Edit Task Modal -->
  <dialog id="edit-task-modal" class="modal">
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4">Edit Task</h3>
      <div class="form-control gap-4">
        <input type="hidden" id="edit-task-id" />
        <input type="hidden" id="edit-task-phase" />
        <div>
          <label class="label"><span class="label-text">Title</span></label>
          <input type="text" id="edit-task-title" class="input input-bordered w-full" />
        </div>
        <div>
          <label class="label"><span class="label-text">Agent Type</span></label>
          <input type="text" id="edit-task-agent" class="input input-bordered w-full" placeholder="e.g., python-backend-engineer" />
        </div>
        <div>
          <label class="label"><span class="label-text">Skill</span></label>
          <input type="text" id="edit-task-skill" class="input input-bordered w-full" placeholder="e.g., test, review, build" />
        </div>
      </div>
      <div class="modal-action">
        <button class="btn btn-primary" onclick="submitEditTask()">Save Changes</button>
        <form method="dialog"><button class="btn">Cancel</button></form>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop"><button>close</button></form>
  </dialog>

  <!-- Prompt Modal -->
  <dialog id="prompt-modal" class="modal">
    <div class="modal-box max-w-3xl">
      <h3 class="font-bold text-lg mb-4" id="modal-title">AI Prompt</h3>
      <div class="bg-base-200 rounded-lg p-4 prompt-text whitespace-pre-wrap" id="modal-prompt"></div>
      <div class="modal-action">
        <button class="btn btn-primary" onclick="copyModalPrompt()">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy
        </button>
        <form method="dialog"><button class="btn">Close</button></form>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop"><button>close</button></form>
  </dialog>

  <footer class="footer footer-center bg-base-100 text-base-content p-4 mt-8">
    <aside><p>Generated from <code class="text-primary">plan.json</code> | Press Ctrl+C in terminal to stop server</p></aside>
  </footer>

  <script>
    function setTheme(theme) { document.documentElement.setAttribute('data-theme', theme); localStorage.setItem('theme', theme); }
    const savedTheme = localStorage.getItem('theme'); if (savedTheme) setTheme(savedTheme);
    let currentPlan = null;

    // API calls
    async function api(action, data = {}) {
      try {
        const response = await fetch('/api/' + action, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        const result = await response.json();
        if (!result.ok) throw new Error(result.error || 'API error');
        return result;
      } catch (err) {
        showToast(err.message, 'error');
        throw err;
      }
    }

    async function taskAction(action, taskId) {
      await api(action, { id: taskId });
      showToast(`Task ${action}`, 'success');
      loadAndRender();
    }

    async function moveTask(taskId, target) {
      await api('move', { id: taskId, target });
      showToast(`Moved to ${target}`, 'success');
      loadAndRender();
    }

    function showAddTaskModal(phaseId) {
      document.getElementById('add-task-phase').value = phaseId;
      document.getElementById('add-task-title').value = '';
      document.getElementById('add-task-agent').value = '';
      document.getElementById('add-task-skill').value = '';
      document.getElementById('add-task-modal').showModal();
    }

    async function submitAddTask() {
      const phase = document.getElementById('add-task-phase').value;
      const title = document.getElementById('add-task-title').value.trim();
      const agent = document.getElementById('add-task-agent').value.trim();
      const skill = document.getElementById('add-task-skill').value.trim();
      if (!title) { showToast('Title required', 'error'); return; }
      await api('add-task', { phase, title, agent: agent || null, skill: skill || null });
      document.getElementById('add-task-modal').close();
      showToast('Task added', 'success');
      loadAndRender();
    }

    function showEditTaskModal(taskId, phaseId) {
      const phase = currentPlan.phases.find(p => p.id === phaseId);
      const task = phase?.tasks.find(t => t.id === taskId);
      if (!task) return;
      document.getElementById('edit-task-id').value = taskId;
      document.getElementById('edit-task-phase').value = phaseId;
      document.getElementById('edit-task-title').value = task.title || '';
      document.getElementById('edit-task-agent').value = task.agent_type || '';
      document.getElementById('edit-task-skill').value = task.skill || '';
      document.getElementById('edit-task-modal').showModal();
    }

    async function submitEditTask() {
      const id = document.getElementById('edit-task-id').value;
      const title = document.getElementById('edit-task-title').value.trim();
      const agent = document.getElementById('edit-task-agent').value.trim();
      const skill = document.getElementById('edit-task-skill').value.trim();
      if (!title) { showToast('Title required', 'error'); return; }
      await api('edit-task', { id, title, agent: agent || null, skill: skill || null });
      document.getElementById('edit-task-modal').close();
      showToast('Task updated', 'success');
      loadAndRender();
    }

    function showTaskActions(taskId, phaseId) {
      const phase = currentPlan.phases.find(p => p.id === phaseId);
      const task = phase?.tasks.find(t => t.id === taskId);
      if (!task) return;

      const status = task.status;
      let actions = '';

      if (status !== 'completed') {
        actions += `<button class="btn btn-success btn-sm w-full mb-2" onclick="taskAction('done', '${taskId}'); document.getElementById('task-modal').close();">Mark Complete</button>`;
      }
      if (status !== 'in_progress') {
        actions += `<button class="btn btn-warning btn-sm w-full mb-2" onclick="taskAction('start', '${taskId}'); document.getElementById('task-modal').close();">Start Task</button>`;
      }
      if (status !== 'blocked') {
        actions += `<button class="btn btn-error btn-sm w-full mb-2" onclick="taskAction('block', '${taskId}'); document.getElementById('task-modal').close();">Mark Blocked</button>`;
      }
      if (status !== 'skipped') {
        actions += `<button class="btn btn-neutral btn-sm w-full mb-2" onclick="taskAction('skip', '${taskId}'); document.getElementById('task-modal').close();">Skip Task</button>`;
      }

      actions += '<div class="divider">Move To</div>';
      actions += `<div class="grid grid-cols-3 gap-2">`;
      if (phaseId !== 'bugs') actions += `<button class="btn btn-outline btn-sm" onclick="moveTask('${taskId}', 'bugs'); document.getElementById('task-modal').close();">Bugs</button>`;
      if (phaseId !== 'deferred') actions += `<button class="btn btn-outline btn-sm" onclick="moveTask('${taskId}', 'deferred'); document.getElementById('task-modal').close();">Deferred</button>`;
      if (phaseId !== 'ideas') actions += `<button class="btn btn-outline btn-sm" onclick="moveTask('${taskId}', 'ideas'); document.getElementById('task-modal').close();">Ideas</button>`;
      actions += `</div>`;

      document.getElementById('task-modal-title').textContent = task.title;
      document.getElementById('task-modal-content').innerHTML = actions;
      document.getElementById('task-modal').showModal();
    }

    async function copyToClipboard(text, label = 'Prompt') {
      try { await navigator.clipboard.writeText(text); showToast(`${label} copied!`, 'success'); }
      catch (err) { showToast('Failed to copy', 'error'); }
    }
    function showToast(message, type = 'info') {
      const container = document.getElementById('toast-container');
      const alertClass = type === 'success' ? 'alert-success' : type === 'error' ? 'alert-error' : 'alert-info';
      const toast = document.createElement('div');
      toast.className = `alert ${alertClass} shadow-lg`;
      toast.innerHTML = `<span>${message}</span>`;
      container.appendChild(toast);
      setTimeout(() => toast.remove(), 2000);
    }
    function generateTaskPrompt(task, phase) {
      const deps = task.depends_on?.length ? `\n\nDependencies: ${task.depends_on.join(', ')} (ensure these are completed first)` : '';
      const subtasks = task.subtasks?.length ? `\n\nSubtasks to complete:\n${task.subtasks.map(s => '- ' + s.title).join('\n')}` : '';
      return `## Task: ${task.title}\n\n**Task ID:** ${task.id}\n**Phase:** ${phase.name}\n**Status:** ${task.status}${task.agent_type ? `\n**Agent Type:** ${task.agent_type}` : ''}${deps}${subtasks}\n\n---\n\n### Instructions\n\nUse \`pv\` (plan-view CLI) to track progress on this task:\n\n\`\`\`bash\n# View current task details\npv get ${task.id}\n\n# Mark task as in-progress when starting\npv start ${task.id}\n\n# Mark task as completed when done\npv done ${task.id}\n\n# If blocked, mark it and add notes\npv block ${task.id}\n\`\`\`\n\n### Implementation\n\nImplement this task. When complete:\n1. Ensure all code follows project conventions\n2. Add tests if applicable\n3. Update the task status using \`pv done ${task.id}\``;
    }
    function generatePhasePrompt(phase) {
      const taskList = phase.tasks.map(t => `- [${t.status === 'completed' ? 'x' : ' '}] ${t.id}: ${t.title}`).join('\n');
      return `## Phase: ${phase.name}\n\n**Phase ID:** ${phase.id}\n**Status:** ${phase.status}\n**Progress:** ${phase.progress.completed}/${phase.progress.total} tasks (${phase.progress.percentage.toFixed(0)}%)\n\n**Description:** ${phase.description}\n\n### Tasks in this phase:\n${taskList}\n\n---\n\n### Instructions\n\nUse \`pv\` (plan-view CLI) to work through this phase:\n\n\`\`\`bash\n# View all tasks in this phase\npv get ${phase.id}\n\n# Get the next available task\npv next\n\n# Start working on a task\npv start <task-id>\n\n# Complete a task\npv done <task-id>\n\`\`\`\n\nWork through the pending tasks in this phase. Prioritize tasks with completed dependencies. Update task status as you progress.`;
    }
    function generateNextTaskPrompt() {
      if (!currentPlan) return '';
      const completedIds = new Set();
      currentPlan.phases.forEach(p => p.tasks.forEach(t => { if (t.status === 'completed') completedIds.add(t.id); }));
      let nextTask = null, nextPhase = null;
      for (const phase of currentPlan.phases) {
        for (const task of phase.tasks) {
          if (task.status === 'pending' || task.status === 'in_progress') {
            const depsComplete = !task.depends_on?.length || task.depends_on.every(d => completedIds.has(d));
            if (depsComplete) { nextTask = task; nextPhase = phase; break; }
          }
        }
        if (nextTask) break;
      }
      if (!nextTask) return 'All tasks completed! No next task available.';
      return generateTaskPrompt(nextTask, nextPhase);
    }
    function showPromptModal(title, prompt) {
      document.getElementById('modal-title').textContent = title;
      document.getElementById('modal-prompt').textContent = prompt;
      document.getElementById('prompt-modal').showModal();
    }
    function copyModalPrompt() { copyToClipboard(document.getElementById('modal-prompt').textContent); }
    function copyTaskPrompt(taskId, phaseId) {
      if (!currentPlan) return;
      const phase = currentPlan.phases.find(p => p.id === phaseId);
      const task = phase?.tasks.find(t => t.id === taskId);
      if (task && phase) copyToClipboard(generateTaskPrompt(task, phase));
    }
    function copyPhasePrompt(phaseId) {
      if (!currentPlan) return;
      const phase = currentPlan.phases.find(p => p.id === phaseId);
      if (phase) copyToClipboard(generatePhasePrompt(phase));
    }
    const statusConfig = {
      completed: { badge: 'badge-success', icon: '✓', text: 'Completed' },
      in_progress: { badge: 'badge-warning', icon: '●', text: 'In Progress' },
      pending: { badge: 'badge-ghost', icon: '○', text: 'Pending' },
      blocked: { badge: 'badge-error', icon: '!', text: 'Blocked' },
      skipped: { badge: 'badge-neutral', icon: '—', text: 'Skipped' }
    };
    function renderHeader(plan) {
      const meta = plan.meta;
      return `<div class="hero bg-base-100 rounded-box shadow-xl"><div class="hero-content text-center py-8"><div><h1 class="text-4xl font-bold">${meta.project}</h1><p class="py-4 text-base-content/70">Version ${meta.version} &bull; Updated ${new Date(meta.updated_at).toLocaleDateString()}</p></div></div></div>`;
    }
    function renderSummary(summary) {
      const progressColor = summary.overall_progress === 100 ? 'progress-success' : summary.overall_progress >= 50 ? 'progress-warning' : 'progress-primary';
      return `<div class="stats stats-vertical lg:stats-horizontal shadow w-full bg-base-100"><div class="stat"><div class="stat-figure text-primary"><svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></div><div class="stat-title">Overall Progress</div><div class="stat-value text-primary">${summary.overall_progress.toFixed(0)}%</div><div class="stat-desc"><progress class="progress ${progressColor} w-32" value="${summary.overall_progress}" max="100"></progress></div></div><div class="stat"><div class="stat-figure text-secondary"><svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg></div><div class="stat-title">Phases</div><div class="stat-value">${summary.total_phases}</div><div class="stat-desc">Total phases</div></div><div class="stat"><div class="stat-figure text-success"><svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg></div><div class="stat-title">Completed</div><div class="stat-value text-success">${summary.completed_tasks}</div><div class="stat-desc">of ${summary.total_tasks} tasks</div></div><div class="stat"><div class="stat-figure text-warning"><div class="radial-progress text-warning" style="--value:${summary.overall_progress}; --size:3rem;" role="progressbar">${summary.total_tasks - summary.completed_tasks}</div></div><div class="stat-title">Remaining</div><div class="stat-value">${summary.total_tasks - summary.completed_tasks}</div><div class="stat-desc">tasks left</div></div></div>`;
    }
    let currentRenderPhase = null;
    function renderTask(task) {
      const status = statusConfig[task.status] || statusConfig.pending;
      const hasSubtasks = task.subtasks && task.subtasks.length > 0;
      const completedSubtasks = hasSubtasks ? task.subtasks.filter(s => s.status === 'completed').length : 0;
      const phaseId = currentRenderPhase?.id || '';
      const isExpanded = task.status === 'in_progress';

      const actionButtons = `
        <div class="flex gap-1">
          <button class="btn btn-ghost btn-xs action-btn" onclick="event.stopPropagation(); showTaskActions('${task.id}', '${phaseId}')" title="Actions">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" /></svg>
          </button>
          <button class="btn btn-ghost btn-xs action-btn" onclick="event.stopPropagation(); showEditTaskModal('${task.id}', '${phaseId}')" title="Edit Task">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
          </button>
          <button class="btn btn-ghost btn-xs copy-btn" onclick="event.stopPropagation(); copyTaskPrompt('${task.id}', '${phaseId}')" title="Copy AI Prompt">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
          </button>
        </div>`;
      const taskMeta = [task.agent_type, task.skill].filter(Boolean).join(' / ');

      if (hasSubtasks) {
        return `<div class="collapse collapse-arrow bg-base-200 rounded-lg task-item"><input type="checkbox" ${isExpanded ? 'checked' : ''} /><div class="collapse-title py-2 px-3 min-h-0"><div class="flex items-start justify-between gap-2"><div class="flex-1"><div class="flex items-center gap-2 flex-wrap"><span class="badge ${status.badge} status-badge">${status.icon} ${status.text}</span><code class="text-xs text-base-content/50">${task.id}</code>${actionButtons}<span class="badge badge-ghost badge-xs">${completedSubtasks}/${task.subtasks.length} subtasks</span></div><p class="mt-1 font-medium">${task.title}</p>${taskMeta ? `<span class="badge badge-outline badge-sm mt-1">${taskMeta}</span>` : ''}</div>${task.depends_on && task.depends_on.length > 0 ? `<div class="tooltip tooltip-left" data-tip="Depends on: ${task.depends_on.join(', ')}"><span class="badge badge-ghost badge-sm">→ ${task.depends_on.length}</span></div>` : ''}</div></div><div class="collapse-content px-3 pb-2"><div class="pl-4 border-l-2 border-base-300 space-y-1">${task.subtasks.map(st => { const stStatus = statusConfig[st.status] || statusConfig.pending; return `<div class="text-sm py-1 flex items-center gap-2"><span class="badge ${stStatus.badge} badge-sm">${stStatus.icon} ${stStatus.text}</span><code class="text-xs text-base-content/40">${st.id}</code><span class="${st.status === 'completed' ? 'line-through text-base-content/50' : ''}">${st.title}</span></div>`; }).join('')}</div></div></div>`;
      }
      return `<div class="task-item bg-base-200 rounded-lg p-3 hover:bg-base-300"><div class="flex items-start justify-between gap-2"><div class="flex-1"><div class="flex items-center gap-2 flex-wrap"><span class="badge ${status.badge} status-badge">${status.icon} ${status.text}</span><code class="text-xs text-base-content/50">${task.id}</code>${actionButtons}</div><p class="mt-1 font-medium">${task.title}</p>${taskMeta ? `<span class="badge badge-outline badge-sm mt-1">${taskMeta}</span>` : ''}</div>${task.depends_on && task.depends_on.length > 0 ? `<div class="tooltip tooltip-left" data-tip="Depends on: ${task.depends_on.join(', ')}"><span class="badge badge-ghost badge-sm">→ ${task.depends_on.length}</span></div>` : ''}</div></div>`;
    }
    function renderPhase(phase) {
      currentRenderPhase = phase;
      const status = statusConfig[phase.status] || statusConfig.pending;
      const isExpanded = phase.status === 'in_progress' || (phase.progress.percentage < 100 && phase.progress.percentage > 0);
      return `<div class="collapse collapse-arrow bg-base-100 shadow-xl phase-card"><input type="checkbox" name="phase-accordion" ${isExpanded ? 'checked' : ''} /><div class="collapse-title pr-12"><div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4"><div><div class="flex items-center gap-2 flex-wrap"><h2 class="text-xl font-semibold">${phase.name}</h2><span class="badge ${status.badge}">${status.text}</span><button class="btn btn-ghost btn-xs copy-btn" onclick="event.stopPropagation(); copyPhasePrompt('${phase.id}')" title="Copy Phase Prompt"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg></button><button class="btn btn-ghost btn-xs action-btn" onclick="event.stopPropagation(); showAddTaskModal('${phase.id}')" title="Add Task"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg></button></div><p class="text-base-content/70 text-sm mt-1">${phase.description}</p></div><div class="flex items-center gap-4"><div class="text-right"><div class="text-2xl font-bold">${phase.progress.percentage.toFixed(0)}%</div><div class="text-xs text-base-content/60">${phase.progress.completed}/${phase.progress.total} tasks</div></div><div class="radial-progress ${phase.progress.percentage === 100 ? 'text-success' : 'text-primary'}" style="--value:${phase.progress.percentage}; --size:4rem; --thickness:4px;" role="progressbar"><span class="text-xs">${phase.progress.completed}/${phase.progress.total}</span></div></div></div></div><div class="collapse-content">${phase.tasks.length > 0 ? `<div class="space-y-2 pt-2">${phase.tasks.map(renderTask).join('')}</div>` : '<div class="text-center text-base-content/50 py-4">No tasks in this phase</div>'}</div></div>`;
    }
    function renderDecisions(decisions) {
      if (!decisions || (!decisions.pending?.length && !decisions.resolved?.length)) return '';
      return `<div class="card bg-base-100 shadow-xl"><div class="card-body"><h2 class="card-title"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>Decisions</h2>${decisions.pending?.length ? `<div class="mt-4"><h3 class="font-semibold text-warning mb-2">Pending Decisions</h3><div class="space-y-3">${decisions.pending.map(d => `<div class="bg-base-200 rounded-lg p-4"><div class="flex items-start gap-2"><span class="badge badge-warning badge-sm">${d.id}</span><div class="flex-1"><p class="font-medium">${d.question}</p><div class="mt-2 flex flex-wrap gap-2">${d.options.map(opt => `<span class="badge ${opt === d.recommended ? 'badge-primary' : 'badge-ghost'} badge-sm">${opt}${opt === d.recommended ? ' (recommended)' : ''}</span>`).join('')}</div>${d.notes ? `<p class="text-sm text-base-content/60 mt-2">${d.notes}</p>` : ''}</div></div></div>`).join('')}</div></div>` : ''}${decisions.resolved?.length ? `<div class="mt-4"><h3 class="font-semibold text-success mb-2">Resolved Decisions</h3><div class="space-y-2">${decisions.resolved.map(d => `<div class="bg-base-200 rounded-lg p-3 opacity-75"><span class="badge badge-success badge-sm">${d.id}</span><span class="ml-2">${d.question}</span><span class="badge badge-outline badge-sm ml-2">${d.decided}</span></div>`).join('')}</div></div>` : ''}</div></div>`;
    }
    function renderBlockers(blockers) {
      if (!blockers || blockers.length === 0) return '';
      const activeBlockers = blockers.filter(b => !b.resolved_at);
      return `<div class="card bg-base-100 shadow-xl"><div class="card-body"><h2 class="card-title text-error"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>Blockers</h2>${activeBlockers.length ? `<div class="space-y-2 mt-2">${activeBlockers.map(b => `<div class="alert alert-error"><span class="font-mono text-sm">${b.id}</span><span>${b.description}</span><span class="badge badge-ghost">${b.affects_tasks.length} tasks affected</span></div>`).join('')}</div>` : '<p class="text-success">No active blockers!</p>'}</div></div>`;
    }
    function renderAIPrompts(plan) {
      const hasRemainingTasks = plan.summary.completed_tasks < plan.summary.total_tasks;
      return `<div class="card bg-gradient-to-br from-primary/10 to-secondary/10 shadow-xl border border-primary/20"><div class="card-body"><h2 class="card-title"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>AI Prompts<span class="badge badge-primary">Quick Copy</span></h2><p class="text-sm text-base-content/70">Copy pre-formatted prompts to use with AI assistants. Includes task context and pv CLI commands.</p><div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4"><div class="card bg-base-100 shadow"><div class="card-body p-4"><h3 class="font-semibold flex items-center gap-2"><span class="badge badge-success badge-sm">Next</span>Next Available Task</h3><p class="text-xs text-base-content/60 mt-1">Ready-to-go prompt for the next task in queue</p><div class="card-actions mt-2">${hasRemainingTasks ? `<button class="btn btn-primary btn-sm flex-1" onclick="copyToClipboard(generateNextTaskPrompt())"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy</button><button class="btn btn-ghost btn-sm" onclick="showPromptModal('Next Task', generateNextTaskPrompt())">View</button>` : '<span class="badge badge-success">All Done!</span>'}</div></div></div><div class="card bg-base-100 shadow"><div class="card-body p-4"><h3 class="font-semibold flex items-center gap-2"><span class="badge badge-secondary badge-sm">Full</span>Full Plan Context</h3><p class="text-xs text-base-content/60 mt-1">Complete plan overview for AI onboarding</p><div class="card-actions mt-2"><button class="btn btn-secondary btn-sm flex-1" onclick="copyToClipboard(generateFullPlanPrompt())"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy</button><button class="btn btn-ghost btn-sm" onclick="showPromptModal('Full Plan', generateFullPlanPrompt())">View</button></div></div></div><div class="card bg-base-100 shadow"><div class="card-body p-4"><h3 class="font-semibold flex items-center gap-2"><span class="badge badge-accent badge-sm">Report</span>Status Report</h3><p class="text-xs text-base-content/60 mt-1">Current progress summary for updates</p><div class="card-actions mt-2"><button class="btn btn-accent btn-sm flex-1" onclick="copyToClipboard(generateStatusPrompt())"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>Copy</button><button class="btn btn-ghost btn-sm" onclick="showPromptModal('Status Report', generateStatusPrompt())">View</button></div></div></div></div><div class="divider text-xs text-base-content/50">Or click the copy icon on any task/phase above</div></div></div>`;
    }
    function generateFullPlanPrompt() {
      if (!currentPlan) return '';
      const meta = currentPlan.meta, summary = currentPlan.summary;
      const phaseOverview = currentPlan.phases.map(p => `### ${p.name} (${p.progress.percentage.toFixed(0)}%)\n${p.description}\nTasks: ${p.tasks.map(t => `\n- [${t.status === 'completed' ? 'x' : ' '}] ${t.id}: ${t.title}`).join('')}`).join('\n\n');
      return `# Project: ${meta.project}\n\n**Version:** ${meta.version}\n**Progress:** ${summary.overall_progress.toFixed(0)}% (${summary.completed_tasks}/${summary.total_tasks} tasks)\n**Updated:** ${new Date(meta.updated_at).toLocaleDateString()}\n\n---\n\n## Plan Overview\n\n${phaseOverview}\n\n---\n\n## Working with this Plan\n\nThis project uses \`pv\` (plan-view) CLI for task tracking:\n\n\`\`\`bash\n# View full plan\npv\n\n# Get next available task\npv next\n\n# View specific task\npv get <task-id>\n\n# Mark task in-progress\npv start <task-id>\n\n# Mark task complete\npv done <task-id>\n\n# If blocked\npv block <task-id>\n\`\`\`\n\nFamiliarize yourself with the plan structure. Start with the next available task based on dependencies, or specify which task to work on.`;
    }
    function generateStatusPrompt() {
      if (!currentPlan) return '';
      const meta = currentPlan.meta, summary = currentPlan.summary;
      const phaseStatus = currentPlan.phases.map(p => `- **${p.name}:** ${p.progress.percentage.toFixed(0)}% (${p.progress.completed}/${p.progress.total})`).join('\n');
      const inProgressTasks = [], blockedTasks = [];
      currentPlan.phases.forEach(p => p.tasks.forEach(t => { if (t.status === 'in_progress') inProgressTasks.push(`${t.id}: ${t.title}`); if (t.status === 'blocked') blockedTasks.push(`${t.id}: ${t.title}`); }));
      return `# Status Report: ${meta.project}\n\n**Overall Progress:** ${summary.overall_progress.toFixed(0)}%\n**Completed:** ${summary.completed_tasks}/${summary.total_tasks} tasks\n**Last Updated:** ${new Date(meta.updated_at).toLocaleString()}\n\n## Phase Progress\n${phaseStatus}\n\n${inProgressTasks.length ? `## In Progress\n${inProgressTasks.map(t => '- ' + t).join('\n')}` : ''}\n\n${blockedTasks.length ? `## Blocked\n${blockedTasks.map(t => '- ' + t).join('\n')}` : ''}\n\n---\n\nUse \`pv\` to view details: \`pv\` for full plan, \`pv next\` for next task.`;
    }
    async function loadAndRender() {
      const loading = document.getElementById('loading');
      const error = document.getElementById('error');
      const content = document.getElementById('content');
      const errorMessage = document.getElementById('error-message');
      loading.classList.remove('hidden');
      content.classList.add('hidden');
      error.classList.add('hidden');
      try {
        const response = await fetch('plan.json?t=' + Date.now());
        if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        const plan = await response.json();
        currentPlan = plan;
        document.getElementById('header').innerHTML = renderHeader(plan);
        document.getElementById('summary').innerHTML = renderSummary(plan.summary);
        document.getElementById('phases').innerHTML = plan.phases.map(renderPhase).join('');
        document.getElementById('decisions').innerHTML = renderDecisions(plan.decisions);
        document.getElementById('blockers').innerHTML = renderBlockers(plan.blockers);
        document.getElementById('ai-prompts').innerHTML = renderAIPrompts(plan);
        loading.classList.add('hidden');
        content.classList.remove('hidden');
      } catch (err) {
        console.error('Failed to load plan:', err);
        errorMessage.textContent = `Failed to load plan.json: ${err.message}`;
        loading.classList.add('hidden');
        error.classList.remove('hidden');
      }
    }
    loadAndRender();
  </script>
</body>
</html>"""


def find_free_port(start: int = 8080, max_attempts: int = 100) -> int:
    """Find an available port starting from start."""
    for port in range(start, start + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found in range {start}-{start + max_attempts}")


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with API endpoints for plan modifications."""

    plan_path: Path = Path("plan.json")

    def log_message(self, format, *args):
        pass  # Suppress request logging

    def do_POST(self):
        """Handle API POST requests."""
        if not self.path.startswith("/api/"):
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return

        action = self.path[5:]  # Remove /api/ prefix

        try:
            result = self._handle_action(action, data)
            self._send_json({"ok": True, **result})
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, 400)

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        response = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

    def _handle_action(self, action: str, data: dict) -> dict:
        """Handle an API action."""
        plan = load_plan(self.plan_path)
        if plan is None:
            raise ValueError("Could not load plan.json")

        task_id = data.get("id")

        if action == "done":
            self._set_task_status(plan, task_id, "completed")
        elif action == "start":
            self._set_task_status(plan, task_id, "in_progress")
        elif action == "block":
            self._set_task_status(plan, task_id, "blocked")
        elif action == "skip":
            self._set_task_status(plan, task_id, "skipped")
        elif action == "move":
            target = data.get("target")
            self._move_task(plan, task_id, target)
        elif action == "add-task":
            phase_id = data.get("phase")
            title = data.get("title")
            agent = data.get("agent")
            skill = data.get("skill")
            self._add_task(plan, phase_id, title, agent, skill)
        elif action == "edit-task":
            task_id = data.get("id")
            title = data.get("title")
            agent = data.get("agent")
            skill = data.get("skill")
            self._edit_task(plan, task_id, title, agent, skill)
        else:
            raise ValueError(f"Unknown action: {action}")

        save_plan(self.plan_path, plan)
        return {}

    def _set_task_status(self, plan: dict, task_id: str, status: str):
        """Set a task's status."""
        result = find_task(plan, task_id)
        if result is None:
            raise ValueError(f"Task not found: {task_id}")
        _, task = result
        task["status"] = status
        if status == "in_progress":
            task.setdefault("tracking", {})["started_at"] = now_iso()
        elif status == "completed":
            task.setdefault("tracking", {})["completed_at"] = now_iso()
            # Cascade to subtasks
            for subtask in task.get("subtasks", []):
                subtask["status"] = "completed"

    def _move_task(self, plan: dict, task_id: str, target: str):
        """Move a task to a different phase."""
        result = find_task(plan, task_id)
        if result is None:
            raise ValueError(f"Task not found: {task_id}")
        source_phase, task = result

        # Find or create target phase
        target_phase = find_phase(plan, target)
        if target_phase is None:
            # Create special phase
            names = {"bugs": "Bugs", "deferred": "Deferred", "ideas": "Ideas"}
            descs = {
                "bugs": "Bug fixes and issue resolution",
                "deferred": "Tasks postponed for later consideration",
                "ideas": "Ideas and suggestions for future consideration",
            }
            target_phase = {
                "id": target,
                "name": names.get(target, target.title()),
                "description": descs.get(target, f"{target.title()} phase"),
                "status": "pending",
                "progress": {"completed": 0, "total": 0, "percentage": 0},
                "tasks": [],
            }
            plan["phases"].append(target_phase)

        # Remove from source
        source_phase["tasks"] = [t for t in source_phase["tasks"] if t["id"] != task_id]

        # Generate new ID
        existing_ids = [t["id"] for t in target_phase["tasks"]]
        counter = 1
        while True:
            new_id = f"{target}.1.{counter}"
            if new_id not in existing_ids:
                break
            counter += 1

        task["id"] = new_id
        task["depends_on"] = []  # Clear dependencies when moving
        target_phase["tasks"].append(task)

    def _add_task(
        self, plan: dict, phase_id: str, title: str, agent: str | None, skill: str | None
    ):
        """Add a new task to a phase."""
        phase = find_phase(plan, phase_id)
        if phase is None:
            raise ValueError(f"Phase not found: {phase_id}")

        # Generate task ID
        existing_ids = [t["id"] for t in phase["tasks"]]
        counter = 1
        while True:
            new_id = f"{phase_id}.1.{counter}"
            if new_id not in existing_ids:
                break
            counter += 1

        task = {
            "id": new_id,
            "title": title,
            "status": "pending",
            "depends_on": [],
            "tracking": {},
        }
        if agent:
            task["agent_type"] = agent
        if skill:
            task["skill"] = skill
        phase["tasks"].append(task)

    def _edit_task(
        self, plan: dict, task_id: str, title: str, agent: str | None, skill: str | None
    ):
        """Edit an existing task's title, agent, and skill."""
        result = find_task(plan, task_id)
        if result is None:
            raise ValueError(f"Task not found: {task_id}")
        _, task = result
        task["title"] = title
        if agent:
            task["agent_type"] = agent
        elif "agent_type" in task:
            del task["agent_type"]
        if skill:
            task["skill"] = skill
        elif "skill" in task:
            del task["skill"]


@require_plan
def cmd_dashboard(plan: dict, args: argparse.Namespace) -> None:
    """Open plan dashboard in browser."""
    plan_dir = args.file.parent
    dashboard_path = plan_dir / "dashboard.html"

    # Write dashboard HTML
    dashboard_path.write_text(DASHBOARD_HTML)

    port = getattr(args, "port", None) or find_free_port()
    url = f"http://localhost:{port}/dashboard.html"

    print(f"Dashboard: {url}")
    print("Press Ctrl+C to stop\n")

    # Change to plan directory so plan.json is served
    os.chdir(plan_dir)

    # Set plan path for handler
    DashboardHandler.plan_path = args.file

    # Open browser
    webbrowser.open(url)

    # Start HTTP server
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
