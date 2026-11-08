import React from "react";
import { Route, Switch } from "react-router-dom";
import "./App.css";
import MainContainer from "./Container/ChatPageContainer/MainContainer";
import LoginPageContainer from "./Container/LoginPageContainer";
import RouteContainer from "./Container/RouteContainer";
import Test from "./Components/UI/TestUI/Snippet/PreviewSide";
// import NavBar from "./Components/NavBar/NavBarTest";

function App() {
  return (
    <div className="App">
      <Switch>
        {/* <Route path="/signin" component={UserBuilder} />*/}
        <Route path="/chat" component={MainContainer} />
        <Route path="/login" exact component={LoginPageContainer} />
        <Route path="/" exact component={RouteContainer} />
        <Route path="/test" exact component={Test} />
      </Switch>
    </div>
  );
}

export default App;
