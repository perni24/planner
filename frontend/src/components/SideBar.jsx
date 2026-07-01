import { Link } from 'react-router-dom';
import { useLanguage } from "../context/useLanguage";

const navItems = [
  { to: '/', labelKey: 'sideBar.project', icon: '□' },
  { to: '/calendar', labelKey: 'sideBar.calendar', icon: '▦' },
  { to: '/settings', labelKey: 'sideBar.settings', icon: '⚙' },
];

function SideBar({ isOpen, onToggle }) {

  const { jsonLanguage } = useLanguage();

  return (
    <aside
      className={`h-full shrink-0 bg-main-card border-r border-main-border shadow-sm transition-all duration-300 ${
        isOpen ? 'w-64' : 'w-16'
      }`}
    >
      <div className={`flex items-center py-6 ${isOpen ? 'justify-between px-6' : 'justify-center px-2'}`}>
        {isOpen && (
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
            {jsonLanguage['sideBar.title']}
          </p>
        )}

        <button
          type="button"
          onClick={onToggle}
          className="flex h-8 w-8 items-center justify-center rounded-full border border-main-border bg-main-card text-main-text shadow-sm transition-colors hover:bg-main-hover hover:text-main-hover-text"
          aria-label={isOpen ? 'Nascondi sidebar' : 'Mostra sidebar'}
          title={isOpen ? 'Nascondi sidebar' : 'Mostra sidebar'}
        >
          {isOpen ? '‹' : '›'}
        </button>
      </div>

      <nav className={isOpen ? 'px-3' : 'px-2'}>
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.to}>
              <Link
                to={item.to}
                className={`flex items-center rounded-lg py-3 text-sm font-medium text-main-text hover:bg-main-hover hover:text-main-hover-text transition-colors ${
                  isOpen ? 'gap-3 px-4' : 'justify-center px-0'
                }`}
                title={jsonLanguage[item.labelKey]}
              >
                <span className="text-xl leading-none" aria-hidden="true">
                  {item.icon}
                </span>
                {isOpen && <span>{jsonLanguage[item.labelKey]}</span>}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}

export default SideBar;
