# auto-labeler

`auto-labeler` is a tool for automatically labeling and archiving emails based on how you've
labeled emails in the past. This is useful for emails which are not strictly spam but also
don't require you to look at them. For example:

- tagging and auto-archiving terms of service updates with "terms"
- tagging recruiting emails with "recruiting" and archiving them after a day
- tagging and auto-archiving sales emails with "sales"

Currently `auto-labeler` only supports Gmail.

To label emails, `auto-labeler` fine-tunes a custom text classification model on your machine
using your already labeled or unlabeled emails. Your data and the resulting model never leaves
your computer.

# Usage

## Label emails that you want auto-labeled

Before using auto-labler you need to have at least one existing label that has been applied to
your emails. To do this, just create a label and tag at least 5 emails with that label. Make
sure you apply the label to any relevant emails in your recent emails, since any unlabeled emails
will be used as examples of emails that shouldn't be labeled.

## Install auto-labeler

The simplest way to install `auto-labler` is via pip

```
python3 -m pip install auto-labeler
```

## Train auto-labeler

To train `auto-labler` the following command:

```
auto-labeler train <label 1> <label 2>
```

The auto-archive duration is how long after emails are auto-labeled they should be archived from
your inbox in hours. Set it to `0` to archive emails as soon as they are labeled, or `-1` to never
archive them automatically. Otherwise it should be a positive number that represents hours to wait
until archiving. Delaying archiving can be 

This will prompt you to link with your Gmail account if you haven't linked it already. Once you've
successfully linked your account it will fetch relevant emails and train a model with the contents
of those emails.

The resulting model will be stored in the default data directory for the current user on your platform.
You can change where this is stored by setting the `AUTO_LABELER_DATA_DIR` environment variable.

## Configuring auto-archiving

By default auto-labeled emails are not archived, meaning you will still see them in your inbox. To
change that run the `auto-archive` command.

```
auto-labeler auto-archive <label name> <archive delay in hours>
```

You can set `auto-labeler` to auto-archive immediately by using a delay of `0`. Otherwise it should
be a positive integer that represents the delay in hours. Set it to `-1` to set it back to the
default behavior of not auto-archiving.

Having a delay is useful for emails that you want to see but dissapear automatically if no action
is taking after some time, or to monitor the quality of the automatic labels. Fixing mislabled emails
will improve the quality of models on future trainings.

To set the behavior for all labels use the special `all` label. For example, to automatically
auto-archive all labeled emails immediately after being labeled run the following command.

```
auto-labeler auto-archive all 0
```

Emails only get auto-archived when running the `label` command (below), so make sure you're running
that command regular as part of a cron job.

To see the configured auto-archive settings run `auto-labeler auto-archive`.

## Auto-labeling emails

To automatically label emails run the following command:

```
auto-labeler label
```

This will fetch emails that you've received since the last time the command has been run and
auto-archive any emails that are due to be archived. To run this every hour you can add this
entry to your crontab.

```
0 * * * * auto-labeler label
```

## Unlinking auto-labler

If you no longer want to use `auto-labeler` and want to unlink from Gmail and clean up any
trained models, run the `unlink` command.

```
auto-labeler unlink
```

## Running on a remote computer

Because `auto-labeler` is a local application, you can only connect it to Gmail from your local
computer. In order to run `auto-labeler` on a remote host, you need to do the following:

1. Install `auto-labeler` on both your local computer and the host you want to run training
and/or labeling on.

2. Run `auto-labeler link` on your local computer. This will go through the OAuth process and
link your Gmail account to `auto-labeler`.

3. Copy the `auto-labeler` data dir to the host you want to train and run `auto-labeler` on. You
can get the location of the data dir by running `auto-labeler data-dir`.

4. On the remote host, put the data you copied from your into `auto-labeler`'s data dir. You can
get this value on the remote host by running `auto-labeler data-dir` like you did on your local
computer.

Once you've done that, you can now run `auto-labeler` remotely.
