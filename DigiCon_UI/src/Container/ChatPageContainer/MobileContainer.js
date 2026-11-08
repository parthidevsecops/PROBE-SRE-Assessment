import React from "react";
import { useState, useEffect } from "react";
import Alert from "react-bootstrap/Alert";
import Layout from "../../HOC/Layout";
import { Route, Switch } from "react-router-dom";
import ChatBoxMobile from "../../Components/ChatPage/ChatPageMobile/ChatMobile";
const ChatPageContainer = () => {
  const [show, setShow] = useState(true);
  const [alert, setAlert] = useState(<div></div>);

  useEffect(() => {
    setTimeout(() => {
      setAlert(
        <Alert variant="success" onClose={() => setShow(false)} dismissible>
          <Alert.Heading>Magnum Script ran Successfully</Alert.Heading>
          <p>You can launch Magnum master server on given IP Address</p>
        </Alert>
      );
    }, 1800000);
  });

  return (
    <React.Fragment>
      {show === true ? alert : <div></div>}
      <Layout>
        <Switch>
          <Route path="/chat" exact component={ChatBoxMobile} />
        </Switch>
      </Layout>
    </React.Fragment>
  );
};

export default ChatPageContainer;
