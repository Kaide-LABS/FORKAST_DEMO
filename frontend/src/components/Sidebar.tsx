'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession, signOut } from 'next-auth/react';

const navigation = [
  { name: 'Dashboard', href: '/' },
  { name: 'My Restaurant', href: '/my-restaurant' },
  { name: 'Competitors', href: '/competitors' },
  { name: 'Alerts', href: '/alerts' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();

  return (
    <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-slate-900">
      <div className="flex flex-col flex-1">
        {/* Logo */}
        <div className="flex items-center h-16 px-6 border-b border-slate-800">
          <span className="text-xl font-bold text-white">Forkast CI</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`
                  flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                  ${isActive
                    ? 'bg-forkast-green-500 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }
                `}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="px-6 py-4 border-t border-slate-800">
          {session?.user && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-full bg-forkast-green-500 flex items-center justify-center text-white text-sm font-medium">
                  {session.user.email?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="text-sm text-slate-300 truncate">
                  {session.user.email?.split('@')[0] || 'User'}
                </span>
              </div>
              <button
                onClick={() => signOut({ callbackUrl: '/sign-in' })}
                className="text-xs text-slate-400 hover:text-white transition-colors"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
