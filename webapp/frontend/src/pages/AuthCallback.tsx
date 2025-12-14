import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setToken } = useAuth();

  useEffect(() => {
    const handleAuth = async () => {
      const token = searchParams.get('token');
      const userId = searchParams.get('user_id');
      const email = searchParams.get('email');
      const username = searchParams.get('username');

      if (token && userId && email && username) {
        // Set authentication
        await setToken(token);

        // Redirect to home
        navigate('/');
      } else {
        // Error: redirect to login
        navigate('/login?error=auth_failed');
      }
    };

    handleAuth();
  }, [searchParams, navigate, setToken]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0f1a]">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
        <p className="text-blue-200">Completing authentication...</p>
      </div>
    </div>
  );
}
