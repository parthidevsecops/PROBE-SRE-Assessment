import React from "react";

import MobileViwe from "../../Service/DetectMobile";
import Container from "./Container";
import MobileContainer from "./MobileContainer";
const MainContainer = () => {
  if (MobileViwe.any()) {
    return <MobileContainer />;
  } else return <Container />;
};

export default MainContainer;
