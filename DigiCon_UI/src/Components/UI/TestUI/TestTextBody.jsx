import React from "react";
import { makeStyles } from "@material-ui/core/styles";
import Grid from "@material-ui/core/Grid";
import Paper from "@material-ui/core/Paper";
// import Jumbotron from "react-bootstrap/Jumbotron";
const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
    // backgroundColor: "red",
  },
  paperstartEnd: {
    height: 600,
    width: 320,
    paddingRight: 10,
  },
  paperMid: {
    height: 600,
    width: 400,
  },
  control: {
    padding: theme.spacing(2),
  },
  paper: {
    backgroundColor: "teal",
    height: 80,
    width: 280,
    margin: 20,
  },
  paperMidRow: {
    height: 90,
    width: 280,
  },
  text: {
    paddingTop: 10,
    textAlign: "center",
  },
  image: {
    height: 400,
    width: 280,
  },
}));

export default function TestTextBody() {
  const spacing = 4;
  const classes = useStyles();
  return (
    <Grid container className={classes.root} spacing={2}>
      <Grid item xs={12}>
        <Grid container justify="center" spacing={spacing}>
          <Grid item className={classes.paperstartEnd}>
            <Grid container justify="center">
              <Grid xs={12} item className={classes.paperMidRow} />
              <Grid xs={12} item>
                <Paper className={classes.paper}>
                  <p className={classes.text}>
                    {" "}
                    I Can Help you with documents for RFP/RFI/RFQ
                  </p>
                </Paper>
              </Grid>
              <Grid xs={12} item className={classes.paperMidRow} />

              <Grid xs={12} item>
                <Paper className={classes.paper}>
                  <p className={classes.text}> I Can Show you demo on magnum</p>
                </Paper>
              </Grid>
            </Grid>
          </Grid>

          <Grid item className={classes.paperMid}>
            <Grid container justify="center">
              <Grid xs={12} item className={classes.image} />

              <Grid xs={12} item>
                <Paper className={classes.paper}>
                  <p className={classes.text}>
                    {" "}
                    I Can Show you demo on Dashboard
                  </p>
                </Paper>
              </Grid>
            </Grid>
          </Grid>
          <Grid item className={classes.paperstartEnd}>
            <Grid container justify="center">
              <Grid xs={12} item className={classes.paperMidRow} />
              <Grid xs={12} item>
                <Paper className={classes.paper}>
                  <p className={classes.text}>
                    {" "}
                    I Can Setup up a DevOps pipeline for you
                  </p>
                </Paper>
              </Grid>
              <Grid xs={12} item className={classes.paperMidRow} />

              <Grid xs={12} item>
                <Paper className={classes.paper}>
                  <p className={classes.text}>
                    {" "}
                    I Can Spinup and destroy instance for you
                  </p>
                </Paper>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
}
