from factory.base import Factory, FactoryOptions, OptionDefault


class ArangoDBOptions(FactoryOptions):
    def _build_default_options(self):
        return super()._build_default_options() + [
            OptionDefault("db_session", None, inherit=True),
        ]

    def _is_declaration(self, name, value):
        if name in ("_id", "_key", "_from", "_to"):
            return True

        return super()._is_declaration(name, value)


class ArangoDBCollectionFactory(Factory):

    _options_class = ArangoDBOptions

    class Meta:
        abstract = True

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        return model_class(*args, **kwargs)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        db_session = getattr(cls._meta, "db_session", None)
        if not db_session:
            raise RuntimeError("no session provided")

        instance = model_class(*args, **kwargs)
        db_session.add(instance)

        return instance


class ArangoDBGraphOptions(ArangoDBOptions):
    def _build_default_options(self):
        """Add "graph" option."""
        return super()._build_default_options() + [
            OptionDefault("graph", None, inherit=True),
        ]


class ArangoDBEdgeFactory(Factory):
    _options_class = ArangoDBGraphOptions

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        db_session = getattr(cls._meta, "db_session", None)
        if not db_session:
            raise RuntimeError("no session provided")

        graph = getattr(cls._meta, "graph", None)
        if not graph:
            raise RuntimeError("no graph provided")

        instance = db_session.add(
            graph(connection=db_session).relation(
                kwargs["_from"],
                model_class,
                kwargs["_to"]
            )
        )

        return instance


class ArangoDBEdgeWithAttrsFactory(ArangoDBEdgeFactory):
    """Edge collection with extra attributes."""
    _options_class = ArangoDBGraphOptions

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        db_session = getattr(cls._meta, "db_session", None)
        if not db_session:
            raise RuntimeError("no session provided")

        graph = getattr(cls._meta, "graph", None)
        if not graph:
            raise RuntimeError("no graph provided")

        _from = kwargs.pop("_from")
        _to = kwargs.pop("_to")

        instance = db_session.add(
            graph(connection=db_session).relation(
                _from,
                model_class(**kwargs),
                _to
            )
        )

        return instance
