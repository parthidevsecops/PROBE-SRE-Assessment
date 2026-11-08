import React, { useState } from "react";

import ChatBox from "../../Components/ChatPage/ChatPageDesktop/ChatBox";
import NavBar from "../../Components/NavBar/NavBar";
import BottomBody from "../../Components/ChatPage/ChatPageDesktop/ChatPageBody/BottomBody";

import io from "socket.io-client";

import apiUrl from "../../Service/api";

import HeadBody from "../../Components/ChatPage/ChatPageDesktop/ChatPageBody/HeadBody";
import Copyright from "../../Components/UI/Copyright";

import { makeStyles } from "@material-ui/core/styles";
import Box from "@material-ui/core/Box";
import Container from "@material-ui/core/Container";
import Grid from "@material-ui/core/Grid";
import Paper from "@material-ui/core/Paper";
import CssBaseline from "@material-ui/core/CssBaseline";

import clsx from "clsx";

import "video-react/dist/video-react.css";

import BotReply from "../../Components/ChatPage/ChatPageDesktop/ChatBboxComponants/BotReply";
import OptionReply from "../../Components/ChatPage/ChatPageDesktop/ChatBboxComponants/OptionReply";
import DocumentReply from "../../Components/ChatPage/ChatPageDesktop/ChatBboxComponants/DocumentReply";
import UserReply from "../../Components/ChatPage/ChatPageDesktop/ChatBboxComponants/UserReply";

import pdfIcon from "../../assets/pdf.png";


const socket = io(apiUrl.baseurl);
const ansibleSocket = io(apiUrl.ansible);

const useStyles = makeStyles((theme) => ({
  root: {
    display: "flex",
    backgroundColor: "#f5f5dc",
  },

  container: {
    paddingTop: theme.spacing(3),
    paddingBottom: theme.spacing(4),
  },

  paper: {
    padding: theme.spacing(0),
    display: "flex",
    flexDirection: "column",
  },

  fixedHeight: {
    height: 500,
    margin: 0,
    width: 870,
  },

  bottomBody: {
    padding: 20,
  },

  video: {
    margin: 0,
  },

  appBarSpacer: theme.mixins.toolbar,

  content: {
    marginLeft: 150,
    flexGrow: 1,
    height: "100vh",
    overflow: "auto",
  },
}));

const ChatPageContainer = () => {
  const classes = useStyles();

  const [currentBodyIndex, setBodyIndex] = useState(0);

  const [
    currentBottomBodyIndex,
    setBottomBodyIndex,
  ] = useState(2);

  let [count, setCount] = useState(0);

  const [openDrawer, setOpenDrawer] = useState(true);

  let [Logs, setLogs] = useState([]);

  const [
    notificationShow,
    setNotification,
  ] = useState(false);

  const [videoUrl, setVideoUrl] = useState(null);

  let [chat, setChat] = useState([]);

  let [typing, setTyping] = useState(false);

  let [msg, setInput] = useState("");

  // Default to true: this deployment only has the PROBE /query backend
  // (no Rasa server is deployed), so the assessment chat should be the
  // default path rather than something the user has to toggle on first.
  const [
    useKnowledgeGraph,
    setUseKnowledgeGraph,
  ] = useState(true);

  const [show, setShow] = useState(false);

  const [anyIndex, setAnyIndex] = useState(0);

  const [labelProps, setLabelProps] = useState([
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
    false,
  ]);

  const [activeStep, setActiveStep] = React.useState(0);

  // =========================================================
  // STEPPER LOGIC
  // =========================================================

  const getSteps = () => {
    return [
      "SSH Keygen",
      "Vms Spinup",
      "Installed Dependencies",
      "Setup Master",
      "Setup Workers",
      "Installed Jenkins",
      "Installed Sonarqube",
      "Installed Nexus",
      "Installed Gitlab",
      "Installed ELK",
    ];
  };

  const steps = getSteps();

  const isStepFailed = (step) => {
    if (!Logs[step]) {
      return false;
    }

    return Logs[step].status;
  };

  const handleNext = () => {
    setActiveStep(
      (prevActiveStep) => prevActiveStep + 1
    );
  };

  // =========================================================
  // ANSIBLE SOCKET
  // =========================================================

  const ansibleConnect = () => {
    ansibleSocket.on("connect", () => {
      console.log(ansibleSocket.connected);
    });

    ansibleSocket.on(
      "response",
      (msg, callback) => {
        console.log(`Lgdata --->> ${msg.msg}`);

        if (msg.type === "update") {
          const message = {
            message: msg.msg,
          };

          rasaEmit(message);
        } else {
          Logs = [...Logs, msg];

          setLogs(Logs);

          if (
            Logs[count] &&
            Logs[count].status === false
          ) {
            setCount(count + 1);

            setActiveStep(
              (prevActiveStep) =>
                prevActiveStep + 1
            );
          }

          setCount(count + 1);
        }
      }
    );
  };

  const sendAnsible = (message) => {
    console.log(
      "Sending Ansible message:",
      message
    );

    ansibleSocket.emit("message", message);
  };

  // =========================================================
  // CHAT STATE
  // =========================================================

  const setMsg = (type, message) => {
    setChat((previousChat) => [
      ...previousChat,
      {
        type: type,
        msg: message,
      },
    ]);
  };

  const setTypingvalue = (value) => {
    setTyping(value);
  };

  const resetChat = () => {
    setChat([]);
    setTyping(false);
    setInput("");
  };

  // =========================================================
  // RASA SOCKET
  // =========================================================

  const rasaEmit = (message) => {
    console.log(
      "Sending message to Rasa:",
      message
    );

    socket.emit("message", message);
  };

  const rasaConnect = () => {
    socket.on("connect", () => {
      console.log(socket.connected);
    });

    socket.on(
      "message",
      (msg, callback) => {
        console.log(msg);

        switch (msg.type) {
          case "video":
            handelChatEvent(1, msg.text);
            break;

          case "list":
            handelChatEvent(6, msg.text);
            break;

          case "spin":
            handelChatEvent(5, msg.text);
            sendAnsible(msg.text);
            break;

          case "chart":
            handelChatEvent(4, {
              pass: msg.Pass,
              fail: msg.Fail,
              label: msg.Date,
            });
            break;

          default:
            break;
        }

        setTimeout(() => {
          setMsg("bot", msg);
          setTypingvalue(false);
        }, 1000);
      }
    );
  };

  // =========================================================
  // INPUT
  // =========================================================

  const onChangeValue = (e) => {
    setInput(e.target.value);
  };

  // =========================================================
  // KNOWLEDGE GRAPH TOGGLE
  // =========================================================

  const onKnowledgeGraphChange = (e) => {
    const checked = e.target.checked;

    setUseKnowledgeGraph(checked);

    console.log(
      "Knowledge Graph:",
      checked
    );
  };

  // =========================================================
  // KNOWLEDGE GRAPH API
  // =========================================================
const askKnowledgeGraph = async (question) => {
  const KG_URL = "/query";

  try {
    console.log("KG URL:", KG_URL);
    console.log("KG QUESTION:", question);

    const response = await fetch(KG_URL, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        question: question,
      }),
    });

    console.log("KG HTTP STATUS:", response.status);

    const rawResponse = await response.text();

    console.log("KG RAW RESPONSE:", rawResponse);

    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}: ${rawResponse}`
      );
    }

    const data = JSON.parse(rawResponse);

    console.log("KG JSON RESPONSE:", data);

    setMsg("bot", {
      type: "text",
      text:
        data.answer ||
        data.response ||
        JSON.stringify(data),
       diagram: data.diagram_path || null,
       diagramType: data.diagram_type || null,
       reportUrl: data.report_url || null,
    });

  } catch (error) {
    console.error("KG FULL ERROR:", error);

    setMsg("bot", {
      type: "text",
      text:
        "Knowledge Graph Error: " +
        error.message,
    });
  } finally {
    setTypingvalue(false);
  }
};
  // =========================================================
  // SEND MESSAGE
  // =========================================================

  const onSendMessgae = (e) => {
    if (e) {
      e.preventDefault();
    }

    const question = msg.trim();

    if (question !== "") {
      setTypingvalue(true);

      setInput("");

      setMsg("user", question);

      if (useKnowledgeGraph) {
        askKnowledgeGraph(question);
      } else {
        const message = {
          message: question,
        };

        rasaEmit(message);
      }
    }

    const form = document.getElementById(
      "form-reset"
    );

    if (form) {
      form.reset();
    }
  };

  // =========================================================
  // CHATBOX DISPLAY
  // =========================================================

  const setChatBoxShow = (value, any) => {
    if (any !== null) {
      setAnyIndex(any);
    } else {
      setShow(value);
      setAnyIndex(any);
    }
  };

  // =========================================================
  // DRAWER
  // =========================================================

  const handleDrawerOpen = () => {
    console.log("------------------->");

    setOpenDrawer(!openDrawer);
  };

  const handleDrawerClose = () => {
    setOpenDrawer(false);
  };

  const fixedHeightPaper = clsx(
    classes.paper,
    classes.fixedHeight
  );

  const handelDrawerClick = (value) => {
    setChatBoxShow(true, null);

    setChatBoxShow(true, 0);

    setChat((previousChat) => [
      ...previousChat,
      {
        type: "user",
        msg: value,
      },
    ]);

    setTypingvalue(true);

    if (useKnowledgeGraph) {
      askKnowledgeGraph(value);
    } else {
      const message = {
        message: value,
      };

      rasaEmit(message);
    }
  };

  // =========================================================
  // CHAT EVENTS
  // =========================================================

  const handelChatEvent = (value, msg) => {
    setVideoUrl(msg);

    setBottomBodyIndex(value);
  };

  const handelNotication = () => {
    console.log(
      "------------------->",
      notificationShow
    );

    setNotification(!notificationShow);
  };

  // =========================================================
  // CHAT RENDERING
  // =========================================================

  let chatValue = chat.map((i, index) => {
    if (i.type === "bot") {
      switch (i.msg.type) {
        case "text":
  return (
    <BotReply
      key={index}
      text={i.msg.text}
      diagram={i.msg.diagram}
      diagramType={i.msg.diagramType}
      reportUrl={i.msg.reportUrl}
    />
  );

        case "option":
          return (
            <OptionReply
              text={i.msg.text}
              key={index}
            />
          );

        case "pdf":
          return (
            <DocumentReply
              name={i.msg.name}
              Icon={pdfIcon}
              text={i.msg.text}
              key={index}
            />
          );

        case "ppt":
          return (
            <DocumentReply
              name={i.msg.name}
              Icon={pdfIcon}
              text={i.msg.text}
              key={index}
            />
          );

        case "xsls":
          return (
            <DocumentReply
              name={i.msg.name}
              Icon={pdfIcon}
              text={i.msg.text}
              key={index}
            />
          );

        case "video":
          return null;

        case "list":
          return null;

        case "spin":
          return null;

        case "chart":
          return null;

        default:
          return (
            <BotReply
              key={index}
              text={i.msg.text}
              reportUrl={i.msg.reportUrl}
            />
          );
      }
    }

    return (
      <UserReply
        key={index}
        text={i.msg}
      />
    );
  });

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className={classes.root}>
      <CssBaseline />

      <NavBar
        handelNotication={handelNotication}
        count={count}
        open={openDrawer}
        handleDrawerClose={handleDrawerClose}
        handleDrawerOpen={handleDrawerOpen}
        handelDrawerClick={handelDrawerClick}
      />

      <ChatBox
        setOpenDrawerValue={setOpenDrawer}
        handelChatEvent={handelChatEvent}
        ansibleConnect={ansibleConnect}
        sendAnsible={sendAnsible}
        rasaConnect={rasaConnect}
        resetChat={resetChat}
        setChatBoxShow={setChatBoxShow}
        show={show}
        typing={typing}
        onChangeValue={onChangeValue}
        onSendMessgae={onSendMessgae}
        useKnowledgeGraph={useKnowledgeGraph}
        onKnowledgeGraphChange={
          onKnowledgeGraphChange
        }
        setTypingvalue={setTypingvalue}
        rasaEmit={rasaEmit}
        chatValue={chatValue}
        anyIndex={anyIndex}
      />

      <main className={classes.content}>
        <div className={classes.appBarSpacer} />

        <Container
          maxWidth="lg"
          className={classes.container}
        >
          <HeadBody
            labelProps={labelProps}
            currentBodyIndex={currentBodyIndex}
            activeStep={activeStep}
            steps={steps}
            isStepFailed={isStepFailed}
          />

          <Box p={1.5} />

          <Grid container spacing={3}>
            <Grid
              item
              xs={12}
              md={8}
              lg={9}
            >
              <Paper
                className={fixedHeightPaper}
              >
                <BottomBody
                  className={
                    classes.bottomBody
                  }
                  currentIndex={
                    currentBottomBodyIndex
                  }
                  videoUrl={videoUrl}
                  Logs={Logs}
                />
              </Paper>
            </Grid>

            <Grid
              item
              xs={12}
              md={4}
              lg={3}
            >
            </Grid>
          </Grid>

          <Box pt={4}>
            <Copyright />
          </Box>
        </Container>
      </main>
    </div>
  );
};

export default ChatPageContainer;