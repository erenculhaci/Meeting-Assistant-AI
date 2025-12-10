import { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon,
  Link as LinkIcon,
  Unlink,
  Users,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Trash2,
  Plus,
  Save,
  ExternalLink
} from 'lucide-react';
import { clsx } from 'clsx';
import {
  getJiraConfig,
  saveJiraConfig,
  deleteJiraConfig,
  getJiraUsers,
  getJiraProjects,
  getUserMappings,
  saveUserMapping,
  deleteUserMapping,
} from '../api';
import type { JiraConfigStatus, JiraUser, JiraProject } from '../types';

export default function JiraSettings() {
  const [config, setConfig] = useState<JiraConfigStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form fields
  const [domain, setDomain] = useState('');
  const [email, setEmail] = useState('');
  const [apiToken, setApiToken] = useState('');
  const [projectKey, setProjectKey] = useState('');

  // Jira data
  const [users, setUsers] = useState<JiraUser[]>([]);
  const [projects, setProjects] = useState<JiraProject[]>([]);
  const [userMappings, setUserMappings] = useState<Record<string, string>>({});

  // New mapping form
  const [newMeetingName, setNewMeetingName] = useState('');
  const [newJiraUserId, setNewJiraUserId] = useState('');

  useEffect(() => {
    loadConfig();
  }, []);

  async function loadConfig() {
    try {
      const configData = await getJiraConfig();
      setConfig(configData);
      
      if (configData.configured) {
        setDomain(configData.domain || '');
        setEmail(configData.email || '');
        setProjectKey(configData.project_key || '');
        
        // Load additional data
        const [usersData, projectsData, mappingsData] = await Promise.all([
          getJiraUsers(),
          getJiraProjects(),
          getUserMappings(),
        ]);
        setUsers(usersData);
        setProjects(projectsData);
        setUserMappings(mappingsData);
      }
    } catch (err) {
      console.error('Failed to load config:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveConfig(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await saveJiraConfig({
        domain,
        email,
        api_token: apiToken,
        project_key: projectKey,
      });
      
      setSuccess(result.message);
      setApiToken(''); // Clear token after save
      await loadConfig(); // Reload to get users/projects
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  }

  async function handleDisconnect() {
    if (!confirm('Are you sure you want to disconnect Jira?')) return;

    try {
      await deleteJiraConfig();
      setConfig({ configured: false });
      setDomain('');
      setEmail('');
      setApiToken('');
      setProjectKey('');
      setUsers([]);
      setProjects([]);
      setUserMappings({});
      setSuccess('Jira disconnected successfully');
    } catch (err) {
      setError('Failed to disconnect Jira');
    }
  }

  async function handleAddMapping() {
    if (!newMeetingName || !newJiraUserId) return;

    try {
      await saveUserMapping({
        meeting_name: newMeetingName,
        jira_account_id: newJiraUserId,
      });
      setUserMappings({ ...userMappings, [newMeetingName]: newJiraUserId });
      setNewMeetingName('');
      setNewJiraUserId('');
    } catch (err) {
      setError('Failed to save mapping');
    }
  }

  async function handleDeleteMapping(meetingName: string) {
    try {
      await deleteUserMapping(meetingName);
      const newMappings = { ...userMappings };
      delete newMappings[meetingName];
      setUserMappings(newMappings);
    } catch (err) {
      setError('Failed to delete mapping');
    }
  }

  const getJiraUserName = (accountId: string) => {
    const user = users.find(u => u.account_id === accountId);
    return user?.display_name || accountId;
  };

  if (loading) {
    return (
      <div className="animate-fadeIn flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Jira Settings</h1>
        <p className="text-gray-600">
          Connect your Jira account to create tasks directly from meeting action items.
        </p>
      </div>

      {/* Status Banner */}
      {config?.configured ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-emerald-900">Jira Connected</h3>
                <p className="text-sm text-emerald-700">
                  {config.domain} • Project: {config.project_key}
                </p>
              </div>
            </div>
            <button
              onClick={handleDisconnect}
              className="inline-flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Unlink className="w-4 h-4" />
              Disconnect
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-amber-900">Jira Not Connected</h3>
              <p className="text-sm text-amber-700">
                Enter your Jira credentials below to enable task creation.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700">{error}</p>
          <button onClick={() => setError(null)} className="ml-auto text-red-500 hover:text-red-700">×</button>
        </div>
      )}
      
      {success && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-6 flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
          <p className="text-sm text-emerald-700">{success}</p>
          <button onClick={() => setSuccess(null)} className="ml-auto text-emerald-500 hover:text-emerald-700">×</button>
        </div>
      )}

      {/* Configuration Form */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden mb-8">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
          <SettingsIcon className="w-5 h-5 text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900">Connection Settings</h2>
        </div>

        <form onSubmit={handleSaveConfig} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Jira Domain
            </label>
            <div className="flex items-center">
              <span className="px-3 py-2 bg-gray-100 border border-r-0 border-gray-300 rounded-l-lg text-gray-500 text-sm">
                https://
              </span>
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="yourcompany.atlassian.net"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-r-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Token
              <a
                href="https://id.atlassian.com/manage-profile/security/api-tokens"
                target="_blank"
                rel="noopener noreferrer"
                className="ml-2 text-indigo-600 hover:text-indigo-700 font-normal"
              >
                Get token →
              </a>
            </label>
            <input
              type="password"
              value={apiToken}
              onChange={(e) => setApiToken(e.target.value)}
              placeholder={config?.configured ? '••••••••••••••••' : 'Enter your API token'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              required={!config?.configured}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Default Project
            </label>
            {config?.configured && projects.length > 0 ? (
              <select
                value={projectKey}
                onChange={(e) => setProjectKey(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              >
                {projects.map(project => (
                  <option key={project.key} value={project.key}>
                    {project.name} ({project.key})
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={projectKey}
                onChange={(e) => setProjectKey(e.target.value.toUpperCase())}
                placeholder="PROJECT"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                required
              />
            )}
          </div>

          <button
            type="submit"
            disabled={saving}
            className={clsx(
              'w-full py-3 rounded-xl font-semibold transition-all duration-200',
              saving
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-200 hover:shadow-xl'
            )}
          >
            {saving ? (
              <span className="inline-flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Connecting...
              </span>
            ) : config?.configured ? (
              <span className="inline-flex items-center gap-2">
                <Save className="w-4 h-4" />
                Update Connection
              </span>
            ) : (
              <span className="inline-flex items-center gap-2">
                <LinkIcon className="w-4 h-4" />
                Connect Jira
              </span>
            )}
          </button>
        </form>
      </div>

      {/* User Mappings */}
      {config?.configured && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
            <Users className="w-5 h-5 text-gray-400" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900">User Mappings</h2>
              <p className="text-sm text-gray-500">
                Map meeting participant names to Jira users for automatic assignment
              </p>
            </div>
          </div>

          <div className="p-6">
            {/* Existing Mappings */}
            {Object.keys(userMappings).length > 0 ? (
              <div className="space-y-2 mb-6">
                {Object.entries(userMappings).map(([meetingName, jiraId]) => (
                  <div
                    key={meetingName}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      <span className="font-medium text-gray-900">{meetingName}</span>
                      <span className="text-gray-400">→</span>
                      <span className="text-gray-600">{getJiraUserName(jiraId)}</span>
                    </div>
                    <button
                      onClick={() => handleDeleteMapping(meetingName)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm mb-6">
                No user mappings configured yet. Add mappings to automatically assign Jira tasks.
              </p>
            )}

            {/* Add New Mapping */}
            <div className="flex gap-3">
              <input
                type="text"
                value={newMeetingName}
                onChange={(e) => setNewMeetingName(e.target.value)}
                placeholder="Meeting name (e.g., Speaker_00, John)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              <select
                value={newJiraUserId}
                onChange={(e) => setNewJiraUserId(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="">Select Jira user...</option>
                {users.map(user => (
                  <option key={user.account_id} value={user.account_id}>
                    {user.display_name}
                  </option>
                ))}
              </select>
              <button
                onClick={handleAddMapping}
                disabled={!newMeetingName || !newJiraUserId}
                className={clsx(
                  'px-4 py-2 rounded-lg transition-colors',
                  newMeetingName && newJiraUserId
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                )}
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
