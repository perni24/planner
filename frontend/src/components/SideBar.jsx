import { Link } from 'react-router-dom';
import { useLanguage } from "../context/useLanguage";
import arrowLeftIcon from '../assets/icons/arrow-left.svg?no-inline';
import arrowRightIcon from '../assets/icons/arrow-right.svg?no-inline';
import calendarIcon from '../assets/icons/calendar.svg?no-inline';
import homeIcon from '../assets/icons/home.svg?no-inline';
import settingsIcon from '../assets/icons/settings.svg?no-inline';

const navItems = [
  { to: '/', labelKey: 'sideBar.project', icon: homeIcon },
  { to: '/calendar', labelKey: 'sideBar.calendar', icon: calendarIcon },
  { to: '/settings', labelKey: 'sideBar.settings', icon: settingsIcon },
];

function SideBar({ isOpen, onToggle }) {

  const { jsonLanguage } = useLanguage();
  const toggleIcon = isOpen ? arrowLeftIcon : arrowRightIcon;

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
          className="flex h-7 w-7 items-center justify-center text-main-text transition duration-200 hover:scale-105 hover:text-main-hover-text"
          aria-label={isOpen ? 'Nascondi sidebar' : 'Mostra sidebar'}
          title={isOpen ? 'Nascondi sidebar' : 'Mostra sidebar'}
        >
          <span
            className="h-full w-full bg-current"
            style={{
              maskImage: `url(${toggleIcon})`,
              WebkitMaskImage: `url(${toggleIcon})`,
              maskRepeat: 'no-repeat',
              WebkitMaskRepeat: 'no-repeat',
              maskPosition: 'center',
              WebkitMaskPosition: 'center',
              maskSize: 'contain',
              WebkitMaskSize: 'contain',
            }}
            aria-hidden="true"
          />
        </button>
      </div>

      <nav className={isOpen ? 'px-3' : 'px-2'}>
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.to}>
              <Link
                to={item.to}
                className={`group flex items-center rounded-lg py-3 text-sm font-medium text-main-text hover:bg-main-hover hover:text-main-hover-text transition-colors ${
                  isOpen ? 'gap-3 px-4' : 'justify-center px-0'
                }`}
                title={jsonLanguage[item.labelKey]}
              >
                <span
                  className="h-7 w-7 shrink-0 bg-current opacity-80 transition duration-200 group-hover:scale-110 group-hover:opacity-100"
                  style={{
                    maskImage: `url(${item.icon})`,
                    WebkitMaskImage: `url(${item.icon})`,
                    maskRepeat: 'no-repeat',
                    WebkitMaskRepeat: 'no-repeat',
                    maskPosition: 'center',
                    WebkitMaskPosition: 'center',
                    maskSize: 'contain',
                    WebkitMaskSize: 'contain',
                  }}
                  aria-hidden="true"
                />
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
