import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ProjectRoute from './routes/ProjectRoute';
import Setting from './pages/Setting';
import Calendar from './pages/Calendar';
import TasksRoute from './routes/TasksRoute';

const router = createBrowserRouter([
  {
    path: "/",
    element: <Dashboard />,
    children:[
      {index: true, element: <ProjectRoute/>},
      {path: "settings", element: <Setting/>},
      {path: "calendar", element: <Calendar/>},
      {path: "tasks/:projectId", element: <TasksRoute/>}
    ]
  },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App
