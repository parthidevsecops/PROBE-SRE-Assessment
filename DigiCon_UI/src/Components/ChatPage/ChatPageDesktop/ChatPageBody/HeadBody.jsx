import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import Stepper from "@material-ui/core/Stepper";
import Step from "@material-ui/core/Step";
import StepLabel from "@material-ui/core/StepLabel";
import { Paper } from "@material-ui/core";
import Typography from "@material-ui/core/Typography";

const useStyles = makeStyles((theme) => ({
  root: {
    width: "100%",
  },

  paper: {
    height: 80,
    backgroundColor: "#fff5be",
  },
  head: {
    fontSize: 28,
    fontWeight: "bold",
    fontFamily: "Candara,arial,helvetica",
    padding: 10,
  },
  completed: {
    display: "inline-block",
  },
  instructions: {
    marginTop: theme.spacing(1),
    marginBottom: theme.spacing(1),
  },
}));

export default function HorizontalNonLinearAlternativeLabelStepper(props) {
  const classes = useStyles();
  // const [Head, setHead] = useState("");
  if (props.currentBodyIndex === 1) {
    return (
      <div className={classes.root}>
        <Paper className="p-3  m-0">
          {" "}
          <Stepper
            activeStep={props.activeStep}
            className="p-0 m-0 "
            alternativeLabel
          >
            {props.steps.map((label, index) => {
              const stepProps = {};
              const labelProps = {};

              labelProps.error = props.labelProps[index];

              return (
                <Step key={label} {...stepProps}>
                  <StepLabel {...labelProps}>{label}</StepLabel>
                </Step>
              );
            })}
          </Stepper>
        </Paper>
      </div>
    );
  } else {
    return (
      <div className={classes.root}>
        {/* <Paper className={`${classes.paper} p-3  m-0`}> */}
        <Typography className={classes.head} style={{ textAlign: "center" }}>
          Hi! I am DigiCon.
        </Typography>
        {/* </Paper> */}
      </div>
    );
  }
}
