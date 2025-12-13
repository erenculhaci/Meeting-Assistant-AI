export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  step: 'upload' | 'transcription' | 'summarization' | 'extraction' | 'done';
  progress: number;
  message: string;
  created_at: string;
  completed_at?: string;
  error?: string;
}

export interface TranscriptSegment {
  speaker: string;
  text: string;
  start: number;
  end: number;
}

export interface TaskItem {
  id: string;
  description: string;
  assignee?: string;
  due_date?: string;
  priority?: 'Low' | 'Medium' | 'High' | 'Critical';
  speaker?: string;
  confidence?: number;
  jira_assignee_id?: string;
  jira_created: boolean;
  jira_key?: string;
}

export interface MeetingSummary {
  status: string;
  title: string;
  overview: string;
  key_points: string[];
  decisions: string[];
  discussion_topics: Array<{ topic: string; summary: string }>;
  next_steps: string[];
  participants: string[];
  metadata: {
    duration: number;
    model: string;
    processing_time: number;
    source_file?: string;
    transcript_segments?: number;
  };
}

export interface MeetingResult {
  job_id: string;
  filename: string;
  duration: number;
  language: string;
  transcript: TranscriptSegment[];
  summary: MeetingSummary;
  tasks: TaskItem[];
  created_at: string;
  processing_time: number;
}

export interface MeetingListItem {
  job_id: string;
  filename: string;
  created_at: string;
  duration: number;
  task_count: number;
}

export interface JiraConfig {
  domain: string;
  email: string;
  api_token: string;
  project_key: string;
}

export interface JiraConfigStatus {
  configured: boolean;
  domain?: string;
  email?: string;
  project_key?: string;
}

export interface JiraUser {
  account_id: string;
  display_name: string;
  email?: string;
  avatar_url?: string;
}

export interface JiraProject {
  key: string;
  name: string;
}

export interface UserMapping {
  meeting_name: string;
  jira_account_id: string;
}

export interface JiraTaskDraft {
  task_id: string;
  summary: string;
  description: string;
  assignee_id?: string;
  due_date?: string;
  priority: string;
  issue_type: string;
  labels: string[];
}

export interface JiraCreateRequest {
  job_id: string;
  tasks: JiraTaskDraft[];
}

export interface JiraCreateResult {
  created: Array<{
    task_id: string;
    jira_key: string;
    jira_url: string;
  }>;
  errors: Array<{
    task_id: string;
    error: string;
  }>;
  success_count: number;
  error_count: number;
}

export interface AssigneeMappings {
  [name: string]: string | null;  // e.g., { "Emily": "emily22", "John": "john_doe" }
}

// Keep SpeakerMappings as alias for backward compatibility
export type SpeakerMappings = AssigneeMappings;

// Authentication Types
export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
