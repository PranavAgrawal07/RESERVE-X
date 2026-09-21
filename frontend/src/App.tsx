import { useState } from "react";
import { ReserveXProvider } from "./context/ReserveXContext";
import { Layout } from "./components/layout/Layout";
import { OverviewPage } from "./pages/OverviewPage";
import { ResourcesPage } from "./pages/ResourcesPage";
import { ReservationsPage } from "./pages/ReservationsPage";
import { RiskPage } from "./pages/RiskPage";
import { ActivityPage } from "./pages/ActivityPage";

function App() {
  const [currentTab, setCurrentTab] = useState("overview");

  const renderPage = () => {
    switch (currentTab) {
      case "overview":
        return <OverviewPage onNavigate={setCurrentTab} />;
      case "resources":
        return <ResourcesPage />;
      case "reservations":
        return <ReservationsPage />;
      case "risk":
        return <RiskPage />;
      case "activity":
        return <ActivityPage />;
      default:
        return <OverviewPage onNavigate={setCurrentTab} />;
    }
  };

  return (
    <ReserveXProvider>
      <Layout currentTab={currentTab} onTabChange={setCurrentTab}>
        {renderPage()}
      </Layout>
    </ReserveXProvider>
  );
}

export default App;
