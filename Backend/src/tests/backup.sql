--
-- PostgreSQL database dump
--

\restrict zElrNeCqcQqpfQ5hBihSr5aKZn7PYXEDmZZIws471bOaVWPfuC1TEzZH38cFol9

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: blockchain; Type: TABLE; Schema: public; Owner: cliente
--

CREATE TABLE public.blockchain (
    id integer NOT NULL,
    block_index integer NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    sender_id integer NOT NULL,
    recipient_id integer NOT NULL,
    message_hash text NOT NULL,
    previous_hash character(64) NOT NULL,
    nonce integer NOT NULL,
    hash character(64) NOT NULL
);


ALTER TABLE public.blockchain OWNER TO cliente;

--
-- Name: blockchain_block_index_seq; Type: SEQUENCE; Schema: public; Owner: cliente
--

CREATE SEQUENCE public.blockchain_block_index_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.blockchain_block_index_seq OWNER TO cliente;

--
-- Name: blockchain_block_index_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cliente
--

ALTER SEQUENCE public.blockchain_block_index_seq OWNED BY public.blockchain.block_index;


--
-- Name: blockchain_id_seq; Type: SEQUENCE; Schema: public; Owner: cliente
--

CREATE SEQUENCE public.blockchain_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.blockchain_id_seq OWNER TO cliente;

--
-- Name: blockchain_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cliente
--

ALTER SEQUENCE public.blockchain_id_seq OWNED BY public.blockchain.id;


--
-- Name: group_members; Type: TABLE; Schema: public; Owner: cliente
--

CREATE TABLE public.group_members (
    id_user integer NOT NULL,
    id_group integer NOT NULL
);


ALTER TABLE public.group_members OWNER TO cliente;

--
-- Name: groups; Type: TABLE; Schema: public; Owner: cliente
--

CREATE TABLE public.groups (
    id integer NOT NULL,
    name character varying(100) NOT NULL
);


ALTER TABLE public.groups OWNER TO cliente;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: cliente
--

CREATE SEQUENCE public.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.groups_id_seq OWNER TO cliente;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cliente
--

ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: cliente
--

CREATE TABLE public.messages (
    id integer NOT NULL,
    sender_id integer NOT NULL,
    recipient_id integer,
    group_id integer,
    ciphertext text NOT NULL,
    encrypted_key text NOT NULL,
    nonce character varying(24) NOT NULL,
    auth_tag character varying(24) NOT NULL,
    signature text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.messages OWNER TO cliente;

--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: cliente
--

CREATE SEQUENCE public.messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messages_id_seq OWNER TO cliente;

--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cliente
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: cliente
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    contrasenas text NOT NULL,
    public_key text NOT NULL,
    encrypted_private_key text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO cliente;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: cliente
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO cliente;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cliente
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: blockchain id; Type: DEFAULT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.blockchain ALTER COLUMN id SET DEFAULT nextval('public.blockchain_id_seq'::regclass);


--
-- Name: blockchain block_index; Type: DEFAULT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.blockchain ALTER COLUMN block_index SET DEFAULT nextval('public.blockchain_block_index_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);


--
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: blockchain; Type: TABLE DATA; Schema: public; Owner: cliente
--

COPY public.blockchain (id, block_index, "timestamp", sender_id, recipient_id, message_hash, previous_hash, nonce, hash) FROM stdin;
1	1	2026-05-19 23:46:16.412084+00	1	1	genesis	0000000000000000000000000000000000000000000000000000000000000000	0	bbd3985ee0b1fd1f6730c03a83ccf90b80a15acc4286b18e739f4577d1f95b6c
2	2	2026-05-19 23:46:47.365024+00	2	3	9ecd016f7c94cb35686366d97c85b2b211f947823c4fde607f02bae5d483a0aa	bbd3985ee0b1fd1f6730c03a83ccf90b80a15acc4286b18e739f4577d1f95b6c	0	a87d43c0cebb0c36125d47f1e07d3404b4e55bdad033a661ebf158a422f09b66
3	3	2026-05-19 23:46:47.378061+00	2	3	9ecd016f7c94cb35686366d97c85b2b211f947823c4fde607f02bae5d483a0aa	a87d43c0cebb0c36125d47f1e07d3404b4e55bdad033a661ebf158a422f09b66	0	261a687fd7c7be5cefaaf695c886774dc726d95ef11cd7729fc3ccd3b396f7bd
4	4	2026-05-19 23:46:47.382596+00	2	3	9ecd016f7c94cb35686366d97c85b2b211f947823c4fde607f02bae5d483a0aa	261a687fd7c7be5cefaaf695c886774dc726d95ef11cd7729fc3ccd3b396f7bd	0	78c379a381aadbc227fe50d9a0db0680d996e6dcab389e5fb271feaf9152391e
5	5	2026-05-20 00:14:00.723079+00	2	3	fee888ceb3db304604c66187f5495eea247bf90bc06be5822685d17cd02cce82	78c379a381aadbc227fe50d9a0db0680d996e6dcab389e5fb271feaf9152391e	0	990438a4df62fbf89b5ac3174584abd28128c7789ff818a9fe7669eeed9786d3
6	6	2026-05-20 00:14:00.727776+00	2	3	fee888ceb3db304604c66187f5495eea247bf90bc06be5822685d17cd02cce82	990438a4df62fbf89b5ac3174584abd28128c7789ff818a9fe7669eeed9786d3	0	5e874cf9269ca53df354dd98a377cf736eb3afa1597d129c3605808f0a8d9d18
7	7	2026-05-20 00:14:00.732808+00	2	3	fee888ceb3db304604c66187f5495eea247bf90bc06be5822685d17cd02cce82	5e874cf9269ca53df354dd98a377cf736eb3afa1597d129c3605808f0a8d9d18	0	065ec883cdaab4aebda5bff0729269448d689a90b288950f9ceb7e2ded68570b
\.


--
-- Data for Name: group_members; Type: TABLE DATA; Schema: public; Owner: cliente
--

COPY public.group_members (id_user, id_group) FROM stdin;
2	1
3	1
3	2
4	2
2	3
3	3
4	3
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: cliente
--

COPY public.groups (id, name) FROM stdin;
1	Grupo Alpha
2	Grupo Beta
3	Grupo General
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: cliente
--

COPY public.messages (id, sender_id, recipient_id, group_id, ciphertext, encrypted_key, nonce, auth_tag, signature, created_at) FROM stdin;
1	2	2	3	q8Lun5sU	Mgix6toiS1xzYuW3aWmkTPycXJRGAJrV3XhCubnfHYQx96WQghWithKhzFi5sJlImvZXG/lJCZvamgbbrTVe5NWECJb7jpuzuqaOPp4wrOU713hf72rbRq22Y/rMEJvVbmRLdq/+iYLn7eGQUX1Ta1LnvRcdIe0Dt3KXl8izRjbI8eZnyrIvZVTukWAIYKwY0J8d9nzLRfkBuWaviCFzlfjKro/2n7FdANf9Y9lVlE4OiIcgdNddFOqubIi0zNmc9kxwMOGgXts3wDfqRke4bY+1sGhwxT2d5lsezO80MANvxEqhA01L/d3P1cReOGW5HLL8ThO/W3UD7XHJ+QhOKg==	/U6xmr9buTaGczEamjHQig==	o4x5ewndED20ZW+GOiyC4g==	VeMeR7iKvJmERhOtFZuhyUFOCVL5+9yuK/dVKiwN7G32BKVRcXygBxKpwA6IJqahLhU1UVqAjyp/6SF8W1U0nR/to+mv78J5xHOhwQiEDMKNTExz3jXPNaCQ808kBwTiMWNRM5pXzDpMw5siUFOYUoy95cpNbJm7Ja/pdPNPWYDctNirj41X4ruWIJUHsBuMHvF3NJk8bV3DKIJi6tORKubOF1cjpnMFCxksro0QjgaYlCOBNyH6r1KSyExyFn3cMKsk57NikDFYdiYvWof7820lNv4H7QamcBXMSqQmyMjZxmkia9SGjLTjfT2RpLEV9Kgd6gDXzhWT1zP6nQec2A==	2026-05-19 23:46:46.963819+00
2	2	3	3	kQkNYyd/	WnMS37x0a3fUtBslx2kpMJNwiusR+mN9h0/NY4ZkiLzb2RJauPRmB2vaZ5jc7GJC7yoj9CI2mKrKxViUZA9ec1GZVrJJc4zxDlLI8g+ENQuXCSV/VsnquEce95KQAPpgIdXJ7eIqiwo0LdR3k1MjUB0rv68R3sjBg9KOY9S4567WlcPAZ5nmsoo02hF1qxGe7Ix2PP+secTBK233LzYhkDlHStMLHE2hupsqgU01dIEm+xIc3NpeqZZ9utGQjlOBFmt2uE0SLxUu15O9eJ3Xlk+j1rDD8AXWELR6wLs5VNHYq2GB3/3X796chmr56H81s4pYNxS1TX3vQZ0r7nlU4g==	yV0CRPdDCfXnNhtfD5PZBQ==	6b7yjKC2uvig3r3JoyFENw==	VeMeR7iKvJmERhOtFZuhyUFOCVL5+9yuK/dVKiwN7G32BKVRcXygBxKpwA6IJqahLhU1UVqAjyp/6SF8W1U0nR/to+mv78J5xHOhwQiEDMKNTExz3jXPNaCQ808kBwTiMWNRM5pXzDpMw5siUFOYUoy95cpNbJm7Ja/pdPNPWYDctNirj41X4ruWIJUHsBuMHvF3NJk8bV3DKIJi6tORKubOF1cjpnMFCxksro0QjgaYlCOBNyH6r1KSyExyFn3cMKsk57NikDFYdiYvWof7820lNv4H7QamcBXMSqQmyMjZxmkia9SGjLTjfT2RpLEV9Kgd6gDXzhWT1zP6nQec2A==	2026-05-19 23:46:47.371688+00
3	2	4	3	wE3hFWdc	z3TYyaHSqtbBTe0Iw5R/en2kv3KdUcLJ4WzTQCV/RuuNhpgxTr33VgCb2vB4GChohxc+16AEn3RAganzl5UKxuD7fy9oK43hq3zjqYIDUY+1XDiOMr6suqC0nqjXNV4kb+Px+tJ26RiFZRt6Qv0T/xoXknWgdRcw9REkwyMzzgYoYzwlwBvWNiGwmIfqrVRc3IIyJLQ8hrrp50M03T1aKRCnPCoYo0FGH0u9cAZPCz7KMqaKd7NXDCiZiu2MuqOWMGDygnZZX2ydEaYkFt3VVZr9tn0VLL0Yt6s9T/UlDxXh2v6raHrrIrtvNizhUOp5zuXLWYWmXcc54Fe5Pu6uyg==	6WOphDcwB1PRJ7Gda3XoVg==	6j2vx2aDgLBYp1TLgEL7Ww==	VeMeR7iKvJmERhOtFZuhyUFOCVL5+9yuK/dVKiwN7G32BKVRcXygBxKpwA6IJqahLhU1UVqAjyp/6SF8W1U0nR/to+mv78J5xHOhwQiEDMKNTExz3jXPNaCQ808kBwTiMWNRM5pXzDpMw5siUFOYUoy95cpNbJm7Ja/pdPNPWYDctNirj41X4ruWIJUHsBuMHvF3NJk8bV3DKIJi6tORKubOF1cjpnMFCxksro0QjgaYlCOBNyH6r1KSyExyFn3cMKsk57NikDFYdiYvWof7820lNv4H7QamcBXMSqQmyMjZxmkia9SGjLTjfT2RpLEV9Kgd6gDXzhWT1zP6nQec2A==	2026-05-19 23:46:47.380993+00
4	2	2	3	PmuFjA==	Br7abUsq/ym+SZyxvR/bs59xUYs9j+0+ufOMXO74gR0KqhWT8Fs2m7B4KPR1Qn4TzfQjIAb5J3EKadouxpW/3aeG3jul2uSIrJrt4W8DZ08nsRE+P++m/LnodhHd91Rcnf+fQ+uKyxYQqljIb99pO+mY0R2VEJy4TGXeJexO2DYBXmf0Z7pIvs6W/SVpg14CVtuStypUNd6R1VN/BTZo4C54wbomMQHdch9Lc0SqOATJihlAETkzOirvQ6f4+tR4syrn7hC8DmIXPLY24F3skxyVSaQPU3LCmOm+dJTWJrgSpJcpYPlNyFLF9HZ2EmyVN4DK/7HjYLymXlPKQeu6+w==	4/MLjrs0OntVX6W2q9CVcg==	ATtcfv7WzcBC0R9QqoSkMw==	LXEcWhHh6iNvJQkQ2HuC5tlslVvXoruMIXN0OJzvbjXtDSI99NgfY5QS6yygIlJLDKSmMjEQX69Nndi7PvrTTvmb8hOnXIlZkDVtws3yeTTq51K4MxeAkFqRORbtfAkqHcwtDyQ12lIyJp2N9NAWlRfuUyF2pjSgCQcUzSAnq04fCJoOgUk89dkNUL41Yz13zsmHfKzz4rA9zCbnFAM9uLUxTiBLffFZk4aP4iY/m4N6s/EEaislUvgM/M0ylg8JtxT+/HV/a0ZFA47r1XbCnW9S/dxPpb/lbo1y+afoy2nRkquXN1igoXCr3TZ0g+j9frWS43XKAhyNRBU0d44VrA==	2026-05-19 23:47:02.449474+00
5	2	3	3	QVOiwA==	Tn1sGGLyzzGUAJIEmrRqnMn7TGo/pZmrw7ygRMWcwCx3haKO7kQzd1YEYDNSmJPPl24vmUjGlVT/9bzuWLA+CTkYmVUBO1NEFpOl7UYWeLitfBR9PV8pGpnt0a5dKEWqAKMECdPh4xvGAN5o3kKKpQpNQwani464Th57twyX4uY/wdJban6qbKZcVfi8nRmfJ+Ej584z0VdgYlTNU5DEqEf7hub7M/mlm7zsYIVufC1k5An2UpnhBbIkyywvU7vGWJXKPpq7fIGmpuDA1zWwNh3EY9v48zOdxQzn3UMamnd4uhOKn/jfnCfg5FVphmtkgcfMcf5YAFaj0cPR9R8j7A==	a1jelMPNKug9EEhaAmrxag==	DRni74p/DCnTBF2VlefB8g==	LXEcWhHh6iNvJQkQ2HuC5tlslVvXoruMIXN0OJzvbjXtDSI99NgfY5QS6yygIlJLDKSmMjEQX69Nndi7PvrTTvmb8hOnXIlZkDVtws3yeTTq51K4MxeAkFqRORbtfAkqHcwtDyQ12lIyJp2N9NAWlRfuUyF2pjSgCQcUzSAnq04fCJoOgUk89dkNUL41Yz13zsmHfKzz4rA9zCbnFAM9uLUxTiBLffFZk4aP4iY/m4N6s/EEaislUvgM/M0ylg8JtxT+/HV/a0ZFA47r1XbCnW9S/dxPpb/lbo1y+afoy2nRkquXN1igoXCr3TZ0g+j9frWS43XKAhyNRBU0d44VrA==	2026-05-20 00:14:00.725282+00
6	2	4	3	UXiCPg==	fbc2iSPNaFvJMSQouzZGVjv1IwD7vNexAZ8flTveSdcPt7+rdDbm9gShI8P1xftzEedqvLcb4yaX9X5lrE5ynew6HZbUST7V4k6Sf8C/Y3XVb5k3ZaZZ7TvmK+Gml+2+x0YOHLzOL0MaZUEBC+HrREzSJq/lLKqhwGIbXojmkaNQ/5DCP4J1aZGAobansA0oECPqONn1IP+GJ38JU9A3FJc8Pa1ksIka3UPnxILrszCb/t6XRoa4Y6YyqX2azDh3y1rPrGHSSBRvUwT5qag0tuC2+9k88mdyhRaZHHx8g0+VWH8Dvc7bTztvxo0NZZNu2EiRo+CGHoUMOoxUrLXTjw==	ZJYwHsHCL3eSTGnOSmndIw==	dOdyvOE/50mYTu+bElCa4w==	LXEcWhHh6iNvJQkQ2HuC5tlslVvXoruMIXN0OJzvbjXtDSI99NgfY5QS6yygIlJLDKSmMjEQX69Nndi7PvrTTvmb8hOnXIlZkDVtws3yeTTq51K4MxeAkFqRORbtfAkqHcwtDyQ12lIyJp2N9NAWlRfuUyF2pjSgCQcUzSAnq04fCJoOgUk89dkNUL41Yz13zsmHfKzz4rA9zCbnFAM9uLUxTiBLffFZk4aP4iY/m4N6s/EEaislUvgM/M0ylg8JtxT+/HV/a0ZFA47r1XbCnW9S/dxPpb/lbo1y+afoy2nRkquXN1igoXCr3TZ0g+j9frWS43XKAhyNRBU0d44VrA==	2026-05-20 00:14:00.730727+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: cliente
--

COPY public.users (id, name, email, contrasenas, public_key, encrypted_private_key, created_at) FROM stdin;
1	Genesis	genesis@system.local				2026-05-19 23:46:07.28981+00
2	Alice López	alice@vaultchain.dev	$argon2id$v=19$m=65536,t=2,p=2$ubDlhTjZBhwVi4eQieM79Q$1h3Ev44BsYS0Kf9nzlF9Z8USi2+lIFFN/vJ5tqEoREE	-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAgZHrfSxLkRPS19y9phnT\n2FVzUss6pDmV42YrfH4XhC4J85lLsJbIei6egSQw8B3ISE0y6G8qaswY7fpGJsvS\nNZMj7SxxfOlgRiEPokvRwNUpEkeuOcXpxp5krNmsnKefVZ+sZk14e4npmS0adnji\nISUfzwJhzzqPpk9LwK29pnhz5DLjoJJkwjSZpZtogegpsRnmvrKFgnAPyjMG+jwL\nIpXxiz8M/Z3eYHEjePADyi9EEWS8JLd7EhN1kqB92SGWBKaBekbhX0Rxht8wPYpu\nLwTF3urbXBKfx7QF083X0Mgwf5zyAlNKnjnj4rujUzWtAFO75cp4Q//haMe3TCuD\noQIDAQAB\n-----END PUBLIC KEY-----	852L/SQ+wNNPigvG9g6vGw==:LS0tLS1CRUdJTiBFTkNSWVBURUQgUFJJVkFURSBLRVktLS0tLQpNSUlGSlRCUEJna3Foa2lHOXcwQkJRMHdRakFoQmdrckJnRUVBZHBIQkFzd0ZBUUlPZk5jTmFZdWRtb0NBa0FBCkFnRUlBZ0VCTUIwR0NXQ0dTQUZsQXdRQktnUVFoL010a0ExWVhOQWpZK0x4NWJzL1NBU0NCTkFQK3RYa0I0WXAKYVh6YS9xQ1NKMWdYYTJyckdoamcrNjM2c2tyQWJJWkkwWkg2UTltWWZNM3FnN3Z1Y3lyZE0zRW1kQm4wT084egpTY1podjVuVzV3REowdFV0R2N6M0tLUE9QOGFuTWd1N3MyekpaMm5RbVA1RERuckRXWnNtSG1DT1p0VlFjdndzClgzQlI5YUJoMHowbXdhaDJFdDFqbGFJTVdMTWFhUEdpYTVXbVh6MVJBTUp0dGFnc2Uyd0c3Z0tmYmZiUEdMQ3cKU1duMVJCNWNGVnZmWHBTdWNab1E4aXpOZGloRGNpTU8rd2lTV1c5a3BJTkd5UnU3T0tuYVRiekQ5K2ZuQy9vZwpVN1N4TG4wNklPVjMvd3htRHc3VTNRd3F5MTBSeWlJc3pBbVdrVWNzMGk2aGxlakJ6SDE3emxXcVFzVzk3bDhiCkVQMldGR3Y3UFM0N0lhYnQ5blEwNE5BZkI2VDQrb3czSGxXekZxc3NrbEE3ekJOOHdkN3RhOHd3VEJ0Y2Q1OFgKNnBpZkdrc2pmbjZQZ2oxY2UvK0lKSTFOZnhGOFpZU3krOTFMMVdQYXFCdjBHR0hrajFydlVobFRrYkl0Y004OQp3T1dNaWlwZitpbmk0TXRVcVROZkN2RnNvV1RORjJFaW8vamtMbnY4OUdHQmdIV0pDQTJHYiswUUpGOE14Z01YCmdCdTFKb3JRcitXZ0ZSdkJBYU10TzZmc0J2WlluZ0JvUEx4SklpQnZKRjJXdU5hV1hCcVZTZmNZWkJLK3ErK1EKS1BlMzltQ2ZxYnhVRjBQRmcrL1V6OER3anVRNmk5SDMrdXhoYzBnWk1DZlM1MmFwY1oyeXdkYy8rWVNTbUFuNQpYRGRlVVlvM3hWRGFMclNwQzQ3bkNhSG5uNHRFQ1RKcVpzUmNQVG9YWnVNODh2S1lwVzNkOXYrb010WVI3cWVHCmNSUGxWQ1MwUmU5dVo1MERZa015clVSdFRUUVI5RlFpZGhUMVU1V2hvbmJEdmpqNytyMkJ4MTd0ek5VTFk4WloKcTNFdGdMMVFWQ0F0SlZLblpCajdBTFp0TTRxeXl5QjNnRWxVZFV5a2NqS2gwUC85UWpZZTRJZGxUNUJtUWRueQpwOWFoQXNzaGlpd2JqUW1VSHN2R3RPNFNORzkvSEhGRTJIVDJzLzN6eEcwd2ZOUWhqZXJ2ckZ6TDlYSXRZQmlJCldndmo3c2RUdGVKSlhaZFlwbEYxeWdMM2JXWHdwUWRpbEhrVlhwQUkrY1BBMlJoUGgzRktCaHZBbzRnaDdYc0MKVnhncG42MmtKYXlpSWN4TlFzdCtocHRmYkRNMWtZNGhiLzdnY2VONHR2K3M5Q1JtQUIyOVJZeXcydGVoNEwzUwpobzVEUTBLUnl2U1IrSmhJSzcwUUVCVmVLMHovRWtuV25zeVpsOSthTDNnbFhETU0xVGJZMndaRFlmbVJEQkNsCjc4a3lab3dqRGJoTUNlZkRDcC93QXZsUDQxMmFhY200WmVqY3duMG1lRHYzOUQ0UjFPbFlMOTJ2d1I0djdXaVYKMXlmOVcrTTZyZWdyQVlnVW1pRkU4SERQZkNpUTVPeWxvRDVZTjIvMGk0NWgvVXZzclYxWjNWMGtoZTlUSmU5VgpxQ1grRmlaK2R4cWdjWStlVUhSSmJ0U1V0YTZUVXdMYkE5OCtuQzVYWE9KUTRONkNqd01qQm5sMUZhSHhLbnhPCkZhcVVQQ0FoSkZXaWxlNnovMVp0NWFIaXNtTU5kZDZaY3Y5dXgveHU4M0RqVHVNS1ZGejloSzR1aitvb2ljVDYKUm40UThtWGg1THNvbE4xeGpncGorK0lIS1JEajdIaDkvSXRJUUt1UmsxdVhuTnhTdGRLYlB1Vk5IY2pHVXFWcgowUGd1a1pmWFMxVUp3TzUvZ3E0andJK1hhQ3E0OHpjSUlXczljaWI2bWJicjhhTkttalhtVWpwamdGRlJSODg5CmRVVC9IWTQ0T3hkSHQ5ZGpDb3NBcUFycCtkQnVGVnAxSXV4VXV6dmI1QUlkU1J0N1lYY29IN2xEb1VIRjFiR0UKbVAwWnBzVnhhNUFnRWxONFJyN1RoT2VUeVRyRTJQMkIwY0tJSUpxa0F1T2Z0dXVWamM5VDJzSjZBNXFManFOcgpGNjhtbmxOQTVpVFZlTGQ0TTBLUWRBZmJaVGMwZys3N09BPT0KLS0tLS1FTkQgRU5DUllQVEVEIFBSSVZBVEUgS0VZLS0tLS0=	2026-05-19 23:46:20.771692+00
3	Bob Martínez	bob@vaultchain.dev	$argon2id$v=19$m=65536,t=2,p=2$VtFv8AQIqVPQVAC/l6JkkA$d06fkI5L1R/Y/JaR3hYQlcGVb0ncwkNr0Eq7uUQIj0U	-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAru7CUc7n1msCEunklnfu\nGzD7h38NhR2iZzq6GdsCcDR5VbYGAsZlse4LGzciWylwVT/CXGifagu+gj/mvfmq\nVhsy0srmDl+uXqx+6U2Dge8HqE7/Wjqw6SrrG8b1g0IyWAzudNypgeIwuI9KFcQ/\n2SRCWWDr8Cwv6mpSqbfxrrfl2Es6kZvP/vUKJ1oOVospAiKiieKWCQGJoxd+jVLi\n9lpBYIPTqF3cYzwjwR3aTyTCU37wkSrYQqF4EKWDbGCjAG3HLzDxe8z2NjDPXZc3\nkqMfM88uV09lNpUaWkKNZPisx3MREsIayavkDJFMK3G/gI9ldx7GrZTFnApiD8WR\n0QIDAQAB\n-----END PUBLIC KEY-----	UewesXrZKcvUVyj6IVyQoQ==:LS0tLS1CRUdJTiBFTkNSWVBURUQgUFJJVkFURSBLRVktLS0tLQpNSUlGSlRCUEJna3Foa2lHOXcwQkJRMHdRakFoQmdrckJnRUVBZHBIQkFzd0ZBUUlSUWlwaTZjWXVQa0NBa0FBCkFnRUlBZ0VCTUIwR0NXQ0dTQUZsQXdRQktnUVF4MzlQUUZEQU9KWCtPNHRJTVE2b1BRU0NCTkJrOUVXUGF5NGoKM0tWZ2UwTkZSVkVBeXlXRlVjMUxmTFZoWFVUaUcwY25DQTNNd0h1dithN0NJTE1HZjhBbzliUVFnQ042b291MgoxSWJYYU9WT0Q2eGxPOXZCYm1Uay8rOHhpdWdlbmN0ZEI0dUVDRWNORUVxMUZ6NTZDVVBQRlBmUXFrVVluMmlpCk0vTVF0YXZJNVBERWp3TVFhd3dLYWVUcUNUMWowNnBvZzBuTEphbTBTZ1JCVDY3TUFSdTREUDRWWi9US3F1SWEKVVoxSUdHNTBHQnlZb1RmcjQxaG1LRXdGUE9SSTFxTGpGRlF5dnZ6NGJJWkN3UTFlRWFYYk0xL2JmaG1pZ1hRdApKVFNPOHJKRDNDZ0dUVS9ZZ0lSaThUL2h1U2xWN2FjSFU0cXRyazVLcFZLdVA1UGlZOTY5ck55a05CNE1OZjFOCld6d0pIbDZvNWxPeTl4YTcyOVBJWHMyUHpRc3U4WmtJUDlHKytKdjFvcWpVdXR0d3JnSUdleWF4RWlpdm5rMFIKbitvbXREaVRLdmpxQWhtSGtnbjg5c2luS2RWME5zZ2lHM1lScEVMQ2QzZkRaUlBuc1I2ZXRDRVJINlJ5RFJaQwpveGNtZ0hBTmlXdXduY0ZhWlV4Vjg2Z295dzFBY2hWR0V3bkJWckRYNjFPbDU4d3p6YllzSThEZ0N3SzFTRU5lCklKUmdkLzhuN3FDLzQ5WG13UGovMkVRdm8vaDhUSUdmbThxVDdrVkR1bUNyMmtPSng3Z0l5bTNOL1dQQ0Uwby8KVTJsUXM5RVFtNExkREN1dE5vS0d5YXozckp5M0NGbS9CNnQxNEVQeUFVc3ROWjl5RENsekdTdlpwYi9xSHlSTgovZFhuTmw4dnhHeVRETWsxUlJvUjNJT0lINlBWb25ZYUo1aGtjVHhidHFhSXZWNE16RlR5NVYrYzdlRy9VbGtjCm02aGZnZEpKcCtlWW42cWRydVAvemZHLzZ4R3hCQjFPWmxUalR6VzM1dndIS3RPQ1ZxeUx6a25iWHNtcTFTakkKZmh5QWJlVnhWM015ellDZmFoRE1LYnQzclhxR0s1TEd2d3pWbzU1WXlXc250dVdleVZUNCt3UzRJL3d6d0lkSQp1S1ZyYnFOM1krU0JpVXVZNndSQmh6bE5KZksvOWdrZEQ3SGFoUGFCbktoMlVkN1ZHWjZla1VHZXphRmlFRlBnCitmS3h1SnNHUGdWUDl6QjROYktLR3NDR0swOFdnTlZCL0xyeE4yVDJCWnhRUFhicFYwKzdORDFDV09tWGk1RGEKbUJxSWFJaWZWU1dRTDg1SnhnOHdzMkVlMDh4NTg4dm0wbHhBS1ZxTlhmOG1SVHRWVDI5aG9GUlpGOUVUWFFnbgplczVaOG5ENDE5ZUowQUNjbm1wWXY5SXpla2ozejRvNHJWekZxZUFwQkFGell3SHVwZUdnLzQ0RDdITnFTWkJWCnNkNjhSM0NLN1czbDNhcmwzRytEK1lxbWRDK0crV0NLUFVFcTZSR21lWmhheHIwM281SXhRWDNMZHpoaERkeXgKN29RVXZaTXZrckhmeHk2L3RIQzB0YXpBQURIRWNUa3BqVFlHQktoQXhhOXREUU4yQWcweTFtaGtlZ2kySDhyZQpsTFhTYnBoNmhHb1h4MEd4eHp2akIzeURPdlBqWEhYcG14S2ViZFdTMTg5TzBLUWdHV0wyc2RsNXJyZnA0ZkJzCjVGSU53M3hFc0Y1cGNLWjBqZ2k1Uy9HZ0ZUYlpKcFpQNHc3bUdhZzhGTmxOVWsvaGFMaVRkUElnejBxdGxmNjEKUUVGQXhLZmI2UmxYWUM1RTRwa0NpaE9jT0hHbVM4Qi96WGlEUjJRTVNwS0M3anNoSzZMbjB1VUFaYVZQamFyQwp2R0NwTUYwOUhvVVdEMFF3OTdNS2tvb2FhbEpzdUwxTll2R1JlWWJQSE8wMi8xR3NGa1MrcjFUMzNqSGlkYWtMCjJLaU10ekpXTjlJejV5OUVmcUp0WEs4cDNKR0xMb3VON3FlOStPL3ByUCtJSDBtSFk1MU04MkFhcDFGS3BMVXAKUXJNMXY2MCtxbHNDL1RRQmd2NDhzWkpnTlRjTnZaQ05FRWxyQzA0TmNtYWV0S3NmNnlsai85TXdEMXJSQmRwYwp2MHNaYkwyZFB3OTdmWW8zdUwvcHNlcjJmeUFINjRUbWZ3PT0KLS0tLS1FTkQgRU5DUllQVEVEIFBSSVZBVEUgS0VZLS0tLS0=	2026-05-19 23:46:21.267137+00
4	Carol Jiménez	carol@vaultchain.dev	$argon2id$v=19$m=65536,t=2,p=2$OMvAJJUufBqYPB0MEPITaw$Yxg4QvCGxk8HAqmJJ6OXGQSKOlqktgPGgIyUTGKP3mk	-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4eE8zScGnlDYQaug2CNI\nQEtLTAzISL+zFlZRdrpGSoUSGU9EmuaW2P6yA0+R5Ldq8f7yoOTsZ9e7SdOryd0P\n2NsJzFCs4P5LE/Q+4HEVMFzDuXgIOZN7L4k2GzX8fJE5lcggLTmzxlkwTjimuOtq\nyRneqZKbXxDgZEnThhjNjZ7kTNDKWpm475CHMsFYOCtg0OY2FzqfrnOZJP9jnuIQ\nFQ9Y5rcZoeh8uWlzqj6z8ea6Eu1sW0BJbJiV3E019TYQWs7Ise/VDr/N+ippyBa8\npsPbLczVRv/UvJKDcZIn6l/CwqbmhQmd56jYE/BZ0Ex4t2ciSUiAeye/8e3GYgLT\nFQIDAQAB\n-----END PUBLIC KEY-----	C3fDg+mTcmCpRKyyacnBKA==:LS0tLS1CRUdJTiBFTkNSWVBURUQgUFJJVkFURSBLRVktLS0tLQpNSUlGSlRCUEJna3Foa2lHOXcwQkJRMHdRakFoQmdrckJnRUVBZHBIQkFzd0ZBUUlRSkhyNnFJWTVkTUNBa0FBCkFnRUlBZ0VCTUIwR0NXQ0dTQUZsQXdRQktnUVFqVFRYNFRNWVFKMVFwVWR4ZkdXMGJRU0NCTkJXaUVVM29pVWgKamlyTktxSkdnTlRhVEpkd0pYYXJ5NXMvVWJYUm1KMVMyaEc0QlBvSnU2WENUejltZjFZZ3lsQnovaXpGdXBDVApNQ3Y0NE9nVlN1VkN3MDFuWXhHRFM5OGxtMStpSHdoVTlZbnNpMzRnSjJLSnN3K1RHeGdXUlR4aUNvNVBvVUs1Cm1ackVKT0czVHVLbndpSWwxanV0bllRcDk4OUtPWG5IbC90VDRVU2lTZVNwajVHci9TN3c0Q2pqblRWckdITEQKbmZQY3dnS1pBOFFScWZsS0drRTNtS0l2VWFtWitCMXNwa0pidjF1TE9ydkFhWXhNM0NEZkxxdHBjMXo0bk51bwprbDJOcjZoSEJXV2hNZjB3ZmxCYlJTNEZNODY1WkhVd1lndzBOQ2lsZ0JNclJJbFNYeFdCZk5uem9lZ3d5RUZzCkFqOGUwSSt1SkFwWDNnb1J5SmY3V3c1ZEd6OForbDdWNHdGVjRZOEs2b29Ob291RGtuZ2EzT1puQkx5NGQ1VjUKbHFtQnZpMkdmZkI5akEwTDZnWGJXNlkwZi9DVmUyVCtQa3RTbU15WGh4ZFErMCtFRmFMb3R6ZWc5U0ZGbE5PRQpZakd3blE0b3NlREhES1htTzRNREs2MUFMbXk1RE9rTm5kZjNrSmg0UVB1M2lkMklPV2dzT1pBQmhWVzJPTzN4ClFualVuVHRySEdpQi8rbXdLT1BGUllKNm03VGY2SXk4RGlGMlRudlJ6UVBrR3ZRcTFJWHJwckpjQmdrOFdxQnoKME9TWXFYRDBPK2x2WmJvYnphSy9NelhnQi9HaWFkRmVxWDdqWW5oSVRGc1dYK2Q3cnZHSnFMWEk4OWZGdnYxMwphT3ltS3NLajg1YTdRQ3pQaDFBYjgzVStiMHVmcDlIQ0UyS2orMm8xQUJRYkRiNzRielA0RTVmZUZDcWZhMGVwCjFXbWpCaFBndlh1UnZDUFZIRUprNzI2cG5NTlJ3cXM1NHVxbkMwSGo1ekFJQW0wTWozcmFJTnIvMFFGT3pRTTIKaVowNldvMXpzeUxiVWI1TlBsL2FvWTBHcFBDbHBseXczSjZVWlBGVkFueGczODJldlJjTkFtYnpYTzg0R0R3WApoSmhpYjh5bEtJZVJJUTdqZWI1RFBqaWpmeGNEUDM2WjFqYUdRMUZmbG1yczNEMTBDYkZTS2lyYTI2dG41UXZoCnlvaE1DOWoxcG4zRlJublFWUTgrK2hXVWNqSGY3M1lLamFwTm5peXBTWnlmdXdWbDZWNjBzVmVGcG1FeDdBdE4KVkR1ZUtTbzJwMUFCbkhZbEdINHFrUVBjWE9YQkgrYU05ZkdSWWcrVUZCaVR0eXMzemVrK1BNMm5iOS9GTXpKdwpBQjJjUzg5aFBLMGFZR09Lc1pheGNtOFd1ajZyTUZnMkNNQ2l2cC83TmdPMkRXaCsxTElNSEE0b1hFNjRIS3NNClJIUzBQYXErcklMdk4yM0pXdXpkQ25PMmQzU0M5bnBMTkhSV2g3cVEwWWM2Mk5wQXdkRFFCVnk0dHYxVVJvVlYKSmE2VTZSVEtUOHlITFo5OEZlOHJ3d2k1eTBYSlFlemRvKy9HT3FrUTE1ekZoUFpMNHdURk1UUFgrMUpIOG1rSQo5K0FvVFVhdy9mWW5tYmM4Y3BpOGFDRG1SNzlzZDJQMVNXc2VFcUhkeUIya0FiQlNYbTM1MXBFSm1SWnhjdVVZCjBOZWNPZlBUbkZ6WkRpOEw0MmRwRzlFQko3Qys2U0Zqakd3Z0hBV1R6RHBYaWdxL2RrelFicHFhSUJDSWlxOTAKaG16MUFvVEVjSGVZd2NZelRpR1hKOFhQNmd5MHovbllVcnhjVFlVaEZDeDJJbTg3Y3RIUng5VFY1MTQ4ZTByVApCblArVEdVM2RQdlIrTzhyTWhiUEZ0RG9DRHRwYnE5YlBNNWVNbGtLUUpuR1lDWEhyOXNCczFIQjU3UzV1M2RjCjU2UkViak5ad0toWkJGU3NBejdPR0Y1RWx3L2N2bkxjcFNYRzA0UUlxMWNXazNUNnBSZUNHMVdDeEtmNlNvVVMKNVdYRkNwZERqanlMaDZwQ3JCNEZ0b1FuNll5RGJjZWpyZnptNWVSU2VtYXFQc1dNWnJQcXNyb1VySXRFc3FESwpxVko3cmVqQ0c5bEZRRG1sRTM2MllxR1RJM05aVkVLbmtBPT0KLS0tLS1FTkQgRU5DUllQVEVEIFBSSVZBVEUgS0VZLS0tLS0=	2026-05-19 23:46:21.623637+00
\.


--
-- Name: blockchain_block_index_seq; Type: SEQUENCE SET; Schema: public; Owner: cliente
--

SELECT pg_catalog.setval('public.blockchain_block_index_seq', 7, true);


--
-- Name: blockchain_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cliente
--

SELECT pg_catalog.setval('public.blockchain_id_seq', 7, true);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cliente
--

SELECT pg_catalog.setval('public.groups_id_seq', 3, true);


--
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cliente
--

SELECT pg_catalog.setval('public.messages_id_seq', 6, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cliente
--

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: blockchain blockchain_block_index_key; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.blockchain
    ADD CONSTRAINT blockchain_block_index_key UNIQUE (block_index);


--
-- Name: blockchain blockchain_hash_key; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.blockchain
    ADD CONSTRAINT blockchain_hash_key UNIQUE (hash);


--
-- Name: blockchain blockchain_pkey; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.blockchain
    ADD CONSTRAINT blockchain_pkey PRIMARY KEY (id);


--
-- Name: groups groups_name_key; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_name_key UNIQUE (name);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: group_members uq_group_member; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT uq_group_member UNIQUE (id_user, id_group);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: blockchain blockchain_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.blockchain
    ADD CONSTRAINT blockchain_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(id);


--
-- Name: blockchain blockchain_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.blockchain
    ADD CONSTRAINT blockchain_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- Name: group_members group_members_id_group_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_id_group_fkey FOREIGN KEY (id_group) REFERENCES public.groups(id);


--
-- Name: group_members group_members_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.group_members
    ADD CONSTRAINT group_members_id_user_fkey FOREIGN KEY (id_user) REFERENCES public.users(id);


--
-- Name: messages messages_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: messages messages_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(id);


--
-- Name: messages messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cliente
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict zElrNeCqcQqpfQ5hBihSr5aKZn7PYXEDmZZIws471bOaVWPfuC1TEzZH38cFol9

