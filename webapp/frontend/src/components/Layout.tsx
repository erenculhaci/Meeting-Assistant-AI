import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Upload, 
  FileText, 
  Settings, 
  Mic,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { clsx } from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Upload Meeting', href: '/upload', icon: Upload },
  { name: 'Meetings', href: '/meetings', icon: FileText },
  { name: 'Jira Settings', href: '/settings', icon: Settings },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50 to-cyan-50 relative overflow-hidden">
      {/* Background decorations */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-cyan-200/30 to-blue-300/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-1/2 -left-20 w-60 h-60 bg-gradient-to-br from-sky-200/30 to-teal-200/30 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute -bottom-20 right-1/3 w-72 h-72 bg-gradient-to-br from-blue-200/20 to-cyan-300/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-white/70 backdrop-blur-2xl border-r border-white/50 shadow-2xl shadow-sky-200/20 z-50">
        {/* Logo */}
        <div className="h-20 flex items-center gap-3 px-6 border-b border-gray-100/50">
          <div className="relative">
            <div className="w-12 h-12 bg-gradient-to-br from-sky-400 via-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg shadow-sky-300/50 transform hover:scale-105 transition-transform duration-300">
              <Mic className="w-6 h-6 text-white" />
            </div>
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-cyan-400 to-teal-400 rounded-full flex items-center justify-center">
              <Sparkles className="w-2.5 h-2.5 text-white" />
            </div>
          </div>
          <div>
            <h1 className="font-bold text-lg bg-gradient-to-r from-sky-600 to-blue-600 bg-clip-text text-transparent">Meeting AI</h1>
            <p className="text-xs text-gray-500">Smart Assistant</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2 mt-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || 
              (item.href !== '/' && location.pathname.startsWith(item.href));
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex items-center gap-3 px-4 py-3.5 rounded-2xl text-sm font-medium transition-all duration-300 group',
                  isActive
                    ? 'bg-gradient-to-r from-sky-500 via-blue-500 to-cyan-500 text-white shadow-lg shadow-sky-300/50 scale-[1.02]'
                    : 'text-gray-600 hover:bg-gradient-to-r hover:from-sky-50 hover:to-cyan-50 hover:text-sky-700 hover:scale-[1.01]'
                )}
              >
                <item.icon className={clsx(
                  'w-5 h-5 transition-transform duration-300',
                  !isActive && 'group-hover:scale-110'
                )} />
                <span>{item.name}</span>
                {isActive && <ChevronRight className="w-4 h-4 ml-auto animate-pulse" />}
              </Link>
            );
          })}
        </nav>

        {/* Version Badge */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="text-center">
            <span className="text-xs text-gray-400">v1.0.0</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="pl-64 relative z-10">
        <div className="min-h-screen p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
