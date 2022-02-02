from arc import callback


@callback.create(inherit=False)
def clean_exit(args, ctx):
    try:
        yield
    except KeyboardInterrupt:
        ctx.exit(0)
