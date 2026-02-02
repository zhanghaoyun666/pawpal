import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Home from './pages/Home';
import PetDetails from './pages/PetDetails';
import Application from './pages/Application';
import Chat from './pages/Chat';
import ChatList from './pages/ChatList';
import Favorites from './pages/Favorites';
import Profile from './pages/Profile';
import Login from './pages/Login';
import Register from './pages/Register';
import AddPet from './pages/AddPet';
import AdoptionHistory from './pages/AdoptionHistory';
import CoordinatorDashboard from './pages/CoordinatorDashboard';
import MyPublications from './pages/MyPublications';
import HelpCenter from './pages/HelpCenter';

const App: React.FC = () => {
  return (
    <AppProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/details/:id" element={<PetDetails />} />
          <Route path="/application" element={<Application />} />
          <Route path="/chat" element={<ChatList />} />
          <Route path="/chat/:id" element={<Chat />} />
          <Route path="/favorites" element={<Favorites />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/add-pet" element={<AddPet />} />
          <Route path="/adoption-history" element={<AdoptionHistory />} />
          <Route path="/coordinator/dashboard" element={<CoordinatorDashboard />} />
          <Route path="/my-publications" element={<MyPublications />} />
          <Route path="/help" element={<HelpCenter />} />
        </Routes>
      </Router>
    </AppProvider>
  );
};

export default App;