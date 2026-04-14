import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Project from './pages/Project';
import Setting from './pages/Setting';
import Calendar from './pages/Calendar';

const router = createBrowserRouter([
  {
    path: "/",
    element: <Dashboard />,
    children:[
      {index: true, element: <Project/>},
      {path: "settings", element: <Setting/>},
      {path: "calendar", element: <Calendar/>}
    ]
  },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App
