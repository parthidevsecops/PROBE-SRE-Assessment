import React from "react";
import { Redirect } from "react-router-dom";
const RouteContainer = () => {
  const token = localStorage.getItem("token");
  let loggedIn = true;
  if (token == null) {
    loggedIn = false;
  }
  if (loggedIn) {
    return <Redirect to="/chat" />;
  } else {
    return <Redirect to="/login" />;
  }
};

export default RouteContainer;
