import { Link } from 'react-router-dom';

function SideBar() {
  return (
    <aside className="w-64 h-full bg-main-card border-r border-main-border shadow-sm">
      <div className="px-6 py-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
          Navigazione
        </p>
      </div>

      <nav className="px-3">
        <ul className="space-y-2">
          <li>
            <Link
              to="/"
              className="block rounded-lg px-4 py-3 text-sm font-medium text-main-text hover:bg-main-hover hover:text-indigo-600 transition-colors"
            >
              Projects
            </Link>
          </li>
          <li>
            <Link
              to="/calendar"
              className="block rounded-lg px-4 py-3 text-sm font-medium text-main-text hover:bg-main-hover hover:text-indigo-600 transition-colors"
            >
              Calendar
            </Link>
          </li>
          <li>
            <Link
              to="/settings"
              className="block rounded-lg px-4 py-3 text-sm font-medium text-main-text hover:bg-main-hover hover:text-indigo-600 transition-colors"
            >
              Settings
            </Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
}

export default SideBar;
