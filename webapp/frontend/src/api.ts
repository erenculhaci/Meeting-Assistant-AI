import axios from 'axios';
import type {
  JobStatus,
  MeetingResult,
  MeetingListItem,
  JiraConfig,
  JiraConfigStatus,
  JiraUser,
  JiraProject,
  JiraCreateRequest,
  JiraCreateResult,
  TaskItem,
  UserMapping,
  SpeakerMappings,
} from './types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Meeting Processing
export async function uploadFile(file: File): Promise<JobStatus> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<JobStatus>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await api.get<JobStatus>(`/jobs/${jobId}`);
  return response.data;
}

export async function getResults(jobId: string): Promise<MeetingResult> {
  const response = await api.get<MeetingResult>(`/results/${jobId}`);
  return response.data;
}

export async function listResults(): Promise<MeetingListItem[]> {
  const response = await api.get<MeetingListItem[]>('/results');
  return response.data;
}

export async function deleteMeeting(jobId: string): Promise<{ status: string; message: string }> {
  const response = await api.delete<{ status: string; message: string }>(`/results/${jobId}`);
  return response.data;
}

export async function updateTask(jobId: string, taskId: string, task: TaskItem): Promise<TaskItem> {
  const response = await api.put<TaskItem>(`/results/${jobId}/tasks/${taskId}`, task);
  return response.data;
}

// Jira Configuration
export async function saveJiraConfig(config: JiraConfig): Promise<{ status: string; message: string }> {
  const response = await api.post<{ status: string; message: string }>('/jira/config', config);
  return response.data;
}

export async function getJiraConfig(): Promise<JiraConfigStatus> {
  const response = await api.get<JiraConfigStatus>('/jira/config');
  return response.data;
}

export async function deleteJiraConfig(): Promise<{ status: string }> {
  const response = await api.delete<{ status: string }>('/jira/config');
  return response.data;
}

// Jira Users & Projects
export async function getJiraUsers(): Promise<JiraUser[]> {
  const response = await api.get<JiraUser[]>('/jira/users');
  return response.data;
}

export async function getJiraProjects(): Promise<JiraProject[]> {
  const response = await api.get<JiraProject[]>('/jira/projects');
  return response.data;
}

// User Mappings
export async function saveUserMapping(mapping: UserMapping): Promise<{ status: string }> {
  const response = await api.post<{ status: string }>('/jira/user-mappings', mapping);
  return response.data;
}

export async function getUserMappings(): Promise<Record<string, string>> {
  const response = await api.get<Record<string, string>>('/jira/user-mappings');
  return response.data;
}

export async function deleteUserMapping(meetingName: string): Promise<{ status: string }> {
  const response = await api.delete<{ status: string }>(`/jira/user-mappings/${encodeURIComponent(meetingName)}`);
  return response.data;
}

// Jira Issue Creation
export async function createJiraIssues(request: JiraCreateRequest): Promise<JiraCreateResult> {
  const response = await api.post<JiraCreateResult>('/jira/create-issues', request);
  return response.data;
}

// Assignee Mappings (for task assignee nicknames)
export async function getAssigneeMappings(jobId: string): Promise<SpeakerMappings> {
  const response = await api.get<SpeakerMappings>(`/meetings/${jobId}/assignees`);
  return response.data;
}

export async function updateAssigneeMappings(jobId: string, mappings: SpeakerMappings): Promise<{ status: string; mappings: SpeakerMappings }> {
  const response = await api.put<{ status: string; mappings: SpeakerMappings }>(`/meetings/${jobId}/assignees`, mappings);
  return response.data;
}

// Legacy aliases
export const getSpeakerMappings = getAssigneeMappings;
export const updateSpeakerMappings = updateAssigneeMappings;

export default api;
