return {
  {
    "mfussenegger/nvim-lint",
    opts = {
      -- Package linting is more expensive than gopls diagnostics.
      events = { "BufWritePost", "BufReadPost" },
      linters = {
        golangcilint = {
          -- Use the rules selected by the project.
          condition = function(ctx)
            return vim.fs.find({ ".golangci.yml", ".golangci.yaml", ".golangci.toml", ".golangci.json" }, {
              path = ctx.dirname,
              upward = true,
            })[1] ~= nil
          end,
        },
      },
    },
  },
}
